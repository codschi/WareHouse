
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.services.ai_service import generate_sql_query, execute_safe_query

router = APIRouter(prefix="/ai", tags=["AI"])

class QuestionRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    sql: str
    results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

@router.post("/query", response_model=QueryResponse)
async def ask_ai(request: QuestionRequest):
    # 1. Generate SQL
    sql = generate_sql_query(request.question)
    
    # Check for generation errors
    if sql.startswith("Error") or "INVALID_QUERY" in sql:
        return QueryResponse(sql=sql, error="Generation failed or invalid query: " + sql)
    
    # 2. Execute SQL
    results_or_error = await execute_safe_query(sql)
    
    if isinstance(results_or_error, dict) and "error" in results_or_error:
        return QueryResponse(sql=sql, error=results_or_error["error"])
        
    return QueryResponse(sql=sql, results=results_or_error)
