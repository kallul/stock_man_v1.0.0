import sys
from unittest.mock import MagicMock
import sqlite3
import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

# Mock missing dependencies
sys.modules['fastapi'] = MagicMock()
sys.modules['pypdf'] = MagicMock()
sys.modules['pandas'] = MagicMock()
sys.modules['chromadb'] = MagicMock()
sys.modules['ollama'] = MagicMock()
sys.modules['uvicorn'] = MagicMock()
sys.modules['requests'] = MagicMock()

import ollama
import chromadb

# Mock Ollama
def mock_chat(model, messages):
    prompt = messages[0]["content"] if messages else ""
    if "You are a query classifier" in prompt:
        return {"message": {"content": "hybrid"}}
    if "You are a SQL expert" in prompt:
        return {"message": {"content": "SELECT * FROM stocks;"}}
    if "You are a Stock Investment Research Assistant" in prompt:
        return {"message": {"content": "*Stock Overview*\nTesla (TSLA) is currently priced at $182.40 with a target price of $210.00, representing an upside of 15.1%.\n\n*Macroeconomic Context*\nInterest rates remain elevated.\n\n*Synthesis*\nTesla's growth may be slower."}}
    return {"message": {"content": "mocked"}}

ollama.chat.side_effect = mock_chat

mock_collection = MagicMock()
mock_collection.count.return_value = 1
mock_collection.query.return_value = {
    "documents": [["Interest rates are expected to remain elevated."]],
    "metadatas": [[{"source": "Q3_Macro_Outlook.pdf", "page": 2}]]
}
mock_chroma_client = MagicMock()
mock_chroma_client.get_or_create_collection.return_value = mock_collection
chromadb.PersistentClient.return_value = mock_chroma_client

from orchestrator import run_query
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

class MockHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/query':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            question = data.get("question", "")
            
            result = run_query(question)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result, indent=2).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run():
    setup_db()
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, MockHandler)
    print('Starting mock server on port 8000...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
