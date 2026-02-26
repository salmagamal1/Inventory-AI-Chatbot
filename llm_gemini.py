from google import genai
import re
from config import MODEL_API_KEY, MODEL_NAME, PROVIDER

class LLMService:
    def __init__(self):
        # Default to gemini-2.5-flash if nothing is in the .env file
        self.model_name = MODEL_NAME if MODEL_NAME else "gemini-2.5-flash"
        
        # Initialize the new Gemini Client
        if PROVIDER.lower() == "gemini" and MODEL_API_KEY:
            self.client = genai.Client(api_key=MODEL_API_KEY)
        else:
            print("Warning: Gemini API Key not found or Provider not set to Gemini.")
            self.client = None

    def generate_sql(self, user_question: str, schema: str) -> str:
        """Generates SQL query from user question using structured prompts."""
        if not self.client:
            return "Error: Gemini client not initialized."
            
        prompt = f"""
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

        Schema: 
        {schema}
        
        Question: 
        {user_question}
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            raw_text = response.text.strip()
            
            # Clean up any markdown blocks just in case
            match = re.search(r'```sql\s*(.*?)\s*```', raw_text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
            
            return raw_text.replace('```', '').strip()

        except Exception as e:
            print("Gemini Error (SQL):", e)
            return None

    def generate_answer(self, user_question: str, db_results: str) -> str:
        """Generates a natural language answer based on database results."""
        if not self.client:
            return "Error: Gemini client not initialized."
            
        prompt = f"""
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
        - YOU MUST REPLY IN ENGLISH ONLY. 

        Must not ->
        - Do not mention "database", "SQL", or "columns".
        - Do not hallucinate numbers.
        - ABSOLUTELY NO EMOJIS, greetings, or conversational filler.
        - DO NOT SPEAK PERSIAN/FARSI.
        
        Note -> If data is empty/error, politely say the info isn't found.

        Question: {user_question}
        Data: {db_results}
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            print("Gemini Error (Answer):", e)
            return "Sorry, I couldn't formulate an answer."

# --- QUICK TEST BLOCK ---
if __name__ == "__main__":
    import db
    
    # Load your real schema from the file so the test is realistic
    try:
        with open("schema.txt", "r") as file:
            schema = file.read()
    except FileNotFoundError:
        # Fallback if the file isn't there
        schema = "CREATE TABLE Assets ( AssetId INT PRIMARY KEY, AssetName NVARCHAR(200), Status VARCHAR(30) );"

    llm = LLMService()
    
    # 1. LET THE USER TYPE THE QUESTION
    print("\n--- Inventory AI Terminal Test ---")
    question = input("Enter your question: ")  # <--- THIS IS THE CHANGE
    
    if not question.strip():
        print("Empty question. Exiting.")
    else:
        print("-" * 30)
        print("Asking Gemini to generate SQL...")
        sql = llm.generate_sql(question, schema)
        print(f"Generated SQL:\n{sql}\n")
        
        print("Running SQL on your real SQL Server...")
        try:
            columns, rows = db.execute_query(sql)
            real_db_results = f"Columns: {columns}\nRows: {rows}"
            print(f"Real Database Results: {real_db_results}\n")
        except Exception as e:
            real_db_results = f"Database Error: {e}"
            print(real_db_results)
        
        print("Asking Gemini to generate a natural answer...")
        answer = llm.generate_answer(question, real_db_results)
        
        print("\n" + "="*50)
        print(f"Final Answer: '{answer}'")
        print("="*50 + "\n")