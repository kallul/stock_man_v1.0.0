import os
import json
import ollama
from dotenv import load_dotenv

load_dotenv()

from config import LLM_MODEL, OLLAMA_BASE_URL
from prompts import INTENT_PROMPT, SYNTHESIS_PROMPT
from retrieval.vector_retriever import retrieve_macro
from retrieval.sql_retriever import retrieve_stocks

os.environ["OLLAMA_HOST"] = OLLAMA_BASE_URL

def classify_intent(query: str) -> str:
    prompt = INTENT_PROMPT.format(query=query)
    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        intent = response["message"]["content"].strip().lower()
        if intent not in ["macro_only", "stock_only", "hybrid"]:
            return "hybrid"
        return intent
    except Exception as e:
        print(f"Error classifying intent: {e}")
        return "hybrid"

def run_query(query: str) -> dict:
    intent = classify_intent(query)
    
    macro_results = []
    stock_results = {"sql": None, "results": []}
    
    if intent in ["macro_only", "hybrid"]:
        macro_results = retrieve_macro(query)
        
    if intent in ["stock_only", "hybrid"]:
        stock_results = retrieve_stocks(query)
        
    # Format macro context
    macro_context = ""
    sources_list = []
    if macro_results:
        for m in macro_results:
            macro_context += f"Source: {m['source']}, Page: {m['page']}\nText: {m['text']}\n\n"
            if m['source'] not in sources_list:
                sources_list.append(m['source'])
                
    # Format stock data
    stock_data = ""
    if stock_results["results"]:
        stock_data = json.dumps(stock_results["results"], indent=2)
        
    user_message = f"<query>{query}</query>\n<macro_context>{macro_context or 'NONE'}</macro_context>\n<stock_data>{stock_data or 'NONE'}</stock_data>"
    
    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYNTHESIS_PROMPT},
                {"role": "user", "content": user_message}
            ]
        )
        answer = response["message"]["content"].strip()
    except Exception as e:
        print(f"Error during synthesis: {e}")
        answer = "I'm sorry, I encountered an error while synthesizing the answer."
        
    return {
        "answer": answer,
        "intent": intent,
        "sources": sources_list,
        "sql_used": stock_results["sql"]
    }

def search_documents(query: str, filename: str = None) -> list[dict]:
    """
    Performs a raw search across documents, optionally filtered by filename.
    Returns snippets and metadata without synthesis.
    """
    return retrieve_macro(query, n_results=10, filename=filename)
