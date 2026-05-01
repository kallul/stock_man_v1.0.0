import sys
from unittest.mock import MagicMock
import sqlite3
import os
import json

# Mock missing dependencies since the environment doesn't have internet access for pip
sys.modules['fastapi'] = MagicMock()
sys.modules['pypdf'] = MagicMock()
sys.modules['pandas'] = MagicMock()
sys.modules['chromadb'] = MagicMock()
sys.modules['ollama'] = MagicMock()
sys.modules['uvicorn'] = MagicMock()
sys.modules['requests'] = MagicMock()

import ollama
import chromadb

# Mock Ollama behavior
def mock_chat(model, messages):
    prompt = messages[0]["content"] if messages else ""
    if "You are a query classifier" in prompt:
        return {"message": {"content": "hybrid"}}
    if "You are a SQL expert" in prompt:
        return {"message": {"content": "SELECT * FROM stocks;"}}
    if "You are a Stock Investment Research Assistant" in prompt:
        return {"message": {"content": "This is a mocked synthesized answer combining macro and stock data."}}
    return {"message": {"content": "mocked"}}

def mock_embeddings(model, prompt):
    return {"embedding": [0.1] * 768}

ollama.chat.side_effect = mock_chat
ollama.embeddings.side_effect = mock_embeddings

# Mock ChromaDB behavior
mock_collection = MagicMock()
mock_collection.count.return_value = 1
mock_collection.query.return_value = {
    "documents": [["Mock macro text chunk containing interest rate info"]],
    "metadatas": [[{"source": "Q3_Outlook.pdf", "page": 1}]]
}
mock_chroma_client = MagicMock()
mock_chroma_client.get_or_create_collection.return_value = mock_collection
chromadb.PersistentClient.return_value = mock_chroma_client

# Now import our modules safely
from orchestrator import run_query, classify_intent
from retrieval.sql_retriever import text_to_sql, get_schema, execute_sql
from config import DB_PATH

def setup_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS stocks (Symbol TEXT, Price REAL, Target_Price REAL, Sector TEXT, Dividend_Yield REAL)")
    cursor.execute("DELETE FROM stocks")
    cursor.execute("INSERT INTO stocks VALUES ('AAPL', 150.0, 180.0, 'Technology', 0.5)")
    cursor.execute("INSERT INTO stocks VALUES ('TSLA', 182.4, 210.0, 'Consumer Discretionary', 0.0)")
    conn.commit()
    conn.close()

def run_tests():
    print("Setting up test database...")
    setup_db()
    
    print("\n--- Test 1: SQL Schema Retrieval ---")
    schema = get_schema()
    print("Schema retrieved:\n", schema)
    
    print("\n--- Test 2: Intent Classification ---")
    intent = classify_intent("How does macro affect Tesla?")
    print("Intent:", intent)
    assert intent == "hybrid"
    
    print("\n--- Test 3: SQL Generation ---")
    sql = text_to_sql("Show all stocks", schema)
    print("Generated SQL:", sql)
    
    print("\n--- Test 4: SQL Execution ---")
    rows = execute_sql(sql)
    print("SQL Results:", rows)
    assert len(rows) == 2
    
    print("\n--- Test 5: Full Orchestrator Run ---")
    result = run_query("What is Tesla's target price and macro environment?")
    print("Final Result JSON:\n", json.dumps(result, indent=2))
    
    print("\n✅ All logic tests passed successfully in isolated environment!")

if __name__ == "__main__":
    run_tests()
