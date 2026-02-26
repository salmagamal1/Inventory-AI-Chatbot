import g4f
import re

class LLMService:
    def __init__(self):
        # You can change this to "gpt-4o" or "gpt-3.5-turbo" depending on what g4f providers support
        self.model = "gpt-4"

    def generate_sql(self, user_question: str, schema: str) -> str:
        """Generates SQL query from user question using structured prompts."""
        system_prompt = """
        Role -> SQL Server expert.
        
        Objective -> Translate user questions into the exact SQL query ("present query").
        
        Instruction -> Write a valid MS SQL SELECT query based on the schema and question.
        
        Examples ->
        Q: "How many assets do I have?"
        SQL: SELECT COUNT(*) AS AssetCount FROM Assets WHERE Status <> 'Disposed';

        Q: "How many assets by site?"
        SQL: SELECT s.SiteName, COUNT(*) AS AssetCount FROM Assets a JOIN Sites s ON s.SiteId = a.SiteId WHERE a.Status <> 'Disposed' GROUP BY s.SiteName ORDER BY AssetCount DESC;
        
        Must ->
        - Return ONLY raw SQL.
        - Exclude 'Disposed' assets using WHERE Status <> 'Disposed' unless asked explicitly.
        
        Must not ->
        - No markdown formatting (do not wrap in ```sql).
        - No explanations or conversational text.
        - No invented columns/tables.
        
        Note -> Read-only SELECT queries only.
        """

        user_prompt = f"""
        Schema: 
        {schema}
        
        Question: 
        {user_question}
        """

        try:
            response = g4f.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0
            )

            raw_text = response.strip()
            
            # Clean up any markdown blocks just in case
            match = re.search(r'```sql\s*(.*?)\s*```', raw_text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
            
            return raw_text.replace('```', '').strip()

        except Exception as e:
            print("g4f Error (SQL):", e)
            return None

    def generate_answer(self, user_question: str, db_results: str) -> str:
        """Generates a natural language answer based on database results."""
        system_prompt = """
        Role -> Inventory AI assistant.
        
        Objective -> Answer user questions clearly using exactly the SQL results.
        
        Instruction -> Draft a short, natural answer summarizing the data.
        
        Examples ->
        Q: "How many assets do I have?"
        Data: [(42,)]
        Answer: "You have 42 assets in your inventory."

        Q: "How many assets by site?"
        Data: [('Main Warehouse', 15), ('Branch Warehouse', 8)]
        Answer: "Here's the asset count by site: Main Warehouse has 15, and Branch Warehouse has 8."
        
        Must ->
        - Base answer STRICTLY on the provided data.
        - ALWAYS include the actual names and numbers from the Data in your final sentence.
        
        Must not ->
        - Do not mention "database", "SQL", or "columns".
        - Do not hallucinate numbers.
        
        Note -> If data is empty/error, politely say the info isn't found.
        """
        
        user_prompt = f"Question: {user_question}\nData: {db_results}"
        
        try:
            response = g4f.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            return response.strip()
        except Exception as e:
            print("g4f Error (Answer):", e)
            return "Sorry, I couldn't formulate an answer."

# --- QUICK TEST BLOCK ---
if __name__ == "__main__":
    import db
    
    # Load real schema for testing
    try:
        with open("schema.txt", "r") as file:
            current_schema = file.read()
    except:
        current_schema = "CREATE TABLE Assets ( AssetId INT, AssetName NVARCHAR(200), Status VARCHAR(30) );"

    llm = LLMService()
    
    print("\n--- Inventory AI Terminal Test (G4F Version) ---")
    # THE INPUT QUESTION
    question = input("Enter your question: ")
    
    if not question.strip():
        print("Empty question. Exiting.")
    else:
        print("-" * 30)
        print("Asking g4f to generate SQL...")
        sql = llm.generate_sql(question, current_schema)
        print(f"Generated SQL:\n{sql}\n")
        
        if sql:
            print("Running SQL on your real SQL Server...")
            try:
                columns, rows = db.execute_query(sql)
                real_db_results = f"Columns: {columns}\nRows: {rows}"
                print(f"Real Database Results: {real_db_results}\n")
            except Exception as e:
                real_db_results = f"Database Error: {e}"
                print(real_db_results)
            
            print("Asking g4f to generate a natural answer...")
            answer = llm.generate_answer(question, real_db_results)
            
            print("\n" + "="*50)
            print(f"Final Answer: '{answer}'")
            print("="*50 + "\n")
        else:
            print("Failed to generate SQL.")