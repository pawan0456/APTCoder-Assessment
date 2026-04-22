from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
import json
import time
from typing import Optional
from database import DatabaseManager
from nlp_to_sql import NLPToSQLConverter

app = FastAPI(title="EdTech NLP-to-SQL API", version="1.0.0")

# Initialize database and NLP converter
db = DatabaseManager()
nlp_converter = NLPToSQLConverter()

# Analytics storage
query_analytics = {
    "total_queries": 0,
    "queries_log": [],
    "keywords_count": {}
}


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    question: str
    generated_sql: str
    result: list or int
    execution_time: float
    timestamp: str


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    db.init_database()
    print("✅ Database initialized")


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Convert natural language question to SQL and execute it.
    
    Example:
    {
        "question": "How many students enrolled in Python courses in 2024?"
    }
    """
    try:
        question = request.question.strip()
        
        if not question:
            raise ValueError("Question cannot be empty")
        
        # Generate SQL from natural language
        sql_query = nlp_converter.convert_to_sql(question)
        
        # Validate that only SELECT queries are allowed
        if not db.is_select_query(sql_query):
            raise ValueError("Only SELECT queries are allowed")
        
        # Execute SQL query with timing
        start_time = time.time()
        result = db.execute_query(sql_query)
        execution_time = time.time() - start_time
        
        # Log analytics
        log_query_analytics(question, sql_query, execution_time)
        
        return QueryResponse(
            question=question,
            generated_sql=sql_query,
            result=result,
            execution_time=round(execution_time, 4),
            timestamp=datetime.now().isoformat()
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/stats")
async def stats_endpoint():
    """
    Get analytics about all queries executed.
    
    Returns:
    - total_queries: Count of all queries executed
    - common_keywords: Most frequently asked topics
    - slowest_query: Query with highest execution time
    - average_execution_time: Mean time for all queries
    """
    if query_analytics["total_queries"] == 0:
        return {
            "total_queries": 0,
            "common_keywords": {},
            "slowest_query": None,
            "average_execution_time": 0.0
        }
    
    # Find slowest query
    slowest = max(query_analytics["queries_log"], key=lambda x: x["execution_time"])
    
    # Calculate average execution time
    avg_time = sum(q["execution_time"] for q in query_analytics["queries_log"]) / len(query_analytics["queries_log"])
    
    # Get top 5 keywords
    sorted_keywords = sorted(query_analytics["keywords_count"].items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "total_queries": query_analytics["total_queries"],
        "common_keywords": dict(sorted_keywords),
        "slowest_query": {
            "question": slowest["question"],
            "execution_time": slowest["execution_time"],
            "timestamp": slowest["timestamp"]
        },
        "average_execution_time": round(avg_time, 4),
        "recent_queries": query_analytics["queries_log"][-5:]  # Last 5 queries
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


def log_query_analytics(question: str, sql_query: str, execution_time: float):
    """Log query for analytics"""
    query_analytics["total_queries"] += 1
    
    # Store query log
    query_analytics["queries_log"].append({
        "question": question,
        "sql": sql_query,
        "execution_time": execution_time,
        "timestamp": datetime.now().isoformat()
    })
    
    # Extract and count keywords
    keywords = extract_keywords(question.lower())
    for keyword in keywords:
        query_analytics["keywords_count"][keyword] = query_analytics["keywords_count"].get(keyword, 0) + 1


def extract_keywords(question: str) -> list:
    """Extract important keywords from question"""
    stop_words = {"how", "many", "what", "in", "for", "the", "a", "an", "is", "are", "were", "was"}
    words = question.split()
    return [w for w in words if w not in stop_words and len(w) > 2]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
