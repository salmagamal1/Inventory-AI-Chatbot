from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, Optional
import time

# Import your working modules
import db
import config
from llm_gemini import LLMService  
from sql_validator import is_safe_sql  # <-- Imported your new security layer!

# --- 1. Define JSON Input / Output Schemas ---
class ChatRequest(BaseModel):
    session_id: str
    message: str
    context: Optional[Dict[str, Any]] = {}

class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatResponse(BaseModel):
    natural_language_answer: str
    sql_query: str
    token_usage: TokenUsage
    latency_ms: int
    provider: str
    model: str
    status: str

# --- 2. Initialize App and Services ---
app = FastAPI(title="Inventory AI API")
llm = LLMService()

# --- 3. Load Your Database Schema ---
with open("schema.txt", "r") as file:
    SCHEMA = file.read()

# --- 4. Home Page Route ---
@app.get("/")
def home_page():
    return {
        "message": "Welcome to the Inventory AI API!", 
        "instructions": "Go to http://127.0.0.1:8000/docs to test the chatbot."
    }

# --- 5. The Core Chat API Endpoint ---
@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    start_time = time.time()
    
    # 1. Ask AI to generate the SQL
    sql_query = llm.generate_sql(request.message, SCHEMA)
    
    # Handle AI generation failure
    if not sql_query:
        latency = int((time.time() - start_time) * 1000)
        return ChatResponse(
            natural_language_answer="Sorry, I could not generate a query for that question.",
            sql_query="",
            token_usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            latency_ms=latency,
            provider=config.PROVIDER.lower() if config.PROVIDER else "gemini",
            model=llm.model_name,
            status="error"
        )

    # 2. VALIDATION LAYER: Check if the SQL is safe using your external script
    if not is_safe_sql(sql_query):
        latency = int((time.time() - start_time) * 1000)
        return ChatResponse(
            natural_language_answer="Security Alert: Blocked an unsafe database operation.",
            sql_query=sql_query,
            token_usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            latency_ms=latency,
            provider=config.PROVIDER.lower() if config.PROVIDER else "gemini",
            model=llm.model_name,
            status="error"
        )

    # 3. Run the SQL on your database
    try:
        columns, rows = db.execute_query(sql_query)
        db_data = f"Columns: {columns}\nRows: {rows}"
        status = "ok"
    except Exception as e:
        db_data = f"Error executing query: {str(e)}"
        status = "error"

    # 4. Ask AI to generate the natural language answer
    answer = llm.generate_answer(request.message, db_data)

    # 5. Calculate Latency and estimate Tokens
    latency = int((time.time() - start_time) * 1000)
    estimated_prompt_tokens = len(request.message + SCHEMA + db_data) // 4
    estimated_completion_tokens = len(answer + sql_query) // 4

    # 6. Return the exact JSON structure required
    return ChatResponse(
        natural_language_answer=answer,
        sql_query=sql_query,
        token_usage=TokenUsage(
            prompt_tokens=estimated_prompt_tokens,
            completion_tokens=estimated_completion_tokens,
            total_tokens=estimated_prompt_tokens + estimated_completion_tokens
        ),
        latency_ms=latency,
        provider=config.PROVIDER.lower() if config.PROVIDER else "gemini", 
        model=llm.model_name,
        status=status
    )