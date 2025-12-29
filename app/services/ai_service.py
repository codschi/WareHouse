
import google.generativeai as genai
from sqlalchemy import text
from app.core.config import GEMINI_API_KEY

# Setup Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY is not set.")
import os

SYSTEM_PROMPT = """
You are a SQL expert for a Warehouse Management System (WMS).
Your task is to convert natural language questions into executable SQL queries.

Database Schema (SQLite/PostgreSQL compatible):
- product (ProductID, prName, prCategory, prSpec)
- supplier (SupplierID, suName, suPhone, suAddress)
- warehouse (WarehouseID, waName, waLocation)
- staff (StaffID, stName, stDept)
- inboundorder (InboundID, ioDate, SupplierID, StaffID)
- inbounddetail (InboundID, ProductID, idQuantity, WarehouseID)
- requisition (ReqID, reDate, reReason, StaffID)
- reqdetail (ReqID, ProductID, rdQuantity, WarehouseID)

Rules:
1. Return ONLY the SQL query. No markdown formatting (```sql), no explanations.
2. Use valid SQL.
3. If the user asks for something dangerous (DROP, DELETE, UPDATE), respond with "INVALID_QUERY".
4. Always limit results to top 20 if likely to be large.
5. Important: Table names are singular (e.g. 'product', not 'products').
6. Important: Primary keys are Capitalized (e.g. 'ProductID', not 'id').
"""

def generate_sql_query(question: str) -> str:
    if not GEMINI_API_KEY:
        return "Error: API Key not configured."
    
    # Dynamic Model Selection
    model_name = "gemini-1.5-flash" # Default fallback
    print("AI Service: Starting model selection...")
    try:
        for m in genai.list_models():
            # print(f"Checking model: {m.name}")
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini' in m.name:
                    model_name = m.name
                    break
    except Exception as e:
        print(f"AI Service Error during model list: {e}")
        pass
        
    print(f"AI Service: Using Model: {model_name}")
    model = genai.GenerativeModel(model_name)
    prompt = f"{SYSTEM_PROMPT}\n\nUser Question: {question}\nSQL Query:"
    
    print(f"AI Service: Sending prompt to LLM...")
    try:
        response = model.generate_content(prompt)
        print(f"AI Service: Response received.")
        sql = response.text.strip()
        # Clean up if model adds backticks despite instructions
        sql = sql.replace("```sql", "").replace("```", "").strip()
        print(f"AI Service: Generated SQL: {sql}")
        return sql
    except Exception as e:
        print(f"AI Service Generation Error: {e}")
        return f"Error calling AI: {str(e)}"

from app.core.database import get_db_session_context

async def execute_safe_query(sql: str):
    """
    Executes the SQL query if it is a safe SELECT statement.
    """
    # 1. Safety Check
    if not sql.lower().startswith("select"):
        return {"error": "Only SELECT queries are allowed for safety."}
    
    if "drop" in sql.lower() or "delete" in sql.lower() or "update" in sql.lower() or "insert" in sql.lower():
         return {"error": "Unsafe query detected."}

    # 2. Execute
    try:
        async with get_db_session_context() as session:
            result = await session.exec(text(sql))
            # Get columns and data
            # session.exec with text() returns a Result object.
            # .mappings() converts rows to dict-like objects
            result = result.mappings().all()
            
            # Convert to plain dicts for JSON serialization
            return [dict(row) for row in result]
            
    except Exception as e:
        print(f"Database Execution Error: {e}")
        return {"error": f"Database error: {str(e)}"}
