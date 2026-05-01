from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
import uvicorn
import shutil
import os
import requests

from orchestrator import run_query, search_documents
from ingest.pdf_ingestor import ingest_pdf
from ingest.csv_ingestor import ingest_csv
from config import OLLAMA_BASE_URL, LLM_MODEL, EMBED_MODEL
from config import AppConfig


app = FastAPI(title = "Stock Investment Research Assistant")

class QueryRequest(BaseModel):
    question: str = Field(
        ..., 
        min_length = 3, 
        max_length = 1000,
        description = "The research question to ask the assistant. It can be about specific stocks, macroeconomic trends, or both (hybrid).",
        examples= [ "What is the price and target for TSLA?", "How does rising inflation impact the technology sector?" ]
    )

class SearchRequest(BaseModel):
    query: str = Field(
        ..., 
        min_length = 2, 
        max_length = 500,
        description = "The keyword or phrase to search for within the indexed PDF documents.",
        examples = ["interest rates", "economic growth forecast"]
    )
    filename: str = Field(
        None, 
        description="Optional: Filter search results to a specific file (e.g., 'Q3_Outlook.pdf').",
        examples=["Eye on the Market.pdf"]
    )


@app.get("/")
async def root():
    return { 
        "name": AppConfig.APP_NAME,
        "version": AppConfig.APP_VERSION,
        "description": AppConfig.APP_DESCRIPTION,
        "author": AppConfig.APP_AUTHOR,
        "author_email": AppConfig.APP_AUTHOR_EMAIL,
        "license": AppConfig.APP_LICENSE,
        "keywords": AppConfig.APP_KEYWORDS,
        "url": AppConfig.APP_URL,
        "debug": AppConfig.APP_DEBUG,
        "env": AppConfig.APP_ENV,
        "message": "Stock Investment Research Assistant API is running"
    }


@app.post("/query")
async def query_endpoint(request: QueryRequest):
    try:
        result = run_query(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        

@app.post("/search")
async def search_endpoint(request: SearchRequest):
    try:
        results = search_documents(request.query, request.filename)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload/document")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
    os.makedirs("stock_assistant/data/pdfs", exist_ok=True)
    temp_path = f"stock_assistant/data/pdfs/{file.filename}"
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        ingest_pdf(temp_path)
        return {"message": "Document ingested successfully", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest PDF: {e}")


@app.post("/upload/csv")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
    os.makedirs("stock_assistant/data", exist_ok=True)
    temp_path = f"stock_assistant/data/{file.filename}"
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        row_count, columns = ingest_csv(temp_path)
        return {"message": "CSV ingested successfully", "rows_ingested": row_count, "columns": columns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest CSV: {e}")

@app.get("/health")
async def health_check():
    try:
        response = requests.get(OLLAMA_BASE_URL)
        if response.status_code == 200:
            return {
                "status": "ok", 
                "llm_model": LLM_MODEL, 
                "embed_model": EMBED_MODEL
            }
        else:
            return {"status": "error", "detail": f"Ollama returned status code {response.status_code}"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ollama is unreachable at {OLLAMA_BASE_URL}: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
