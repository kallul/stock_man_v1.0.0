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

_KEEP_COLUMNS = [
    "Ticker", "Company", "Sector - Level 1", "Region", "Issuer Country", "Currency",
    "Recommendation", "Price", "Target Price", "Dividend Yield", "Beta",
    "Market Capitalization", "Price to Earning Forward 12M", "Return on Equity FY1",
    "Net Debt to EBITDA FY1", "EBITDA Margin Forward 12M", "Net Profit Margin Forward 12M",
    "Relative Performance YTD",
]
_MAX_ROWS = 15

_PCT_COLUMNS = {"Dividend Yield", "Return on Equity FY1", "EBITDA Margin Forward 12M",
                "Net Profit Margin Forward 12M", "Relative Performance YTD"}

def _format_value(col: str, val) -> str:
    if val is None:
        return "—"
    if col in _PCT_COLUMNS:
        return f"{val * 100:.2f}%"
    if isinstance(val, float):
        return f"{val:,.2f}"
    return str(val)

def _format_stock_table(results: list[dict]) -> str:
    """Render stock results as a compact markdown table for LLM synthesis."""
    rows = results[:_MAX_ROWS]
    # Determine which columns actually have data
    present_cols = [c for c in _KEEP_COLUMNS if any(r.get(c) is not None for r in rows)]
    header = " | ".join(present_cols)
    separator = " | ".join(["---"] * len(present_cols))
    lines = [header, separator]
    for row in rows:
        cells = [_format_value(c, row.get(c)) for c in present_cols]
        lines.append(" | ".join(cells))
    return "\n".join(lines)

def _slim_results(results: list[dict]) -> list[dict]:
    keep = set(_KEEP_COLUMNS)
    return [{k: v for k, v in row.items() if k in keep} for row in results[:_MAX_ROWS]]

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

    # Format stock data as a readable table rather than raw JSON
    stock_data = ""
    if stock_results["results"]:
        stock_data = _format_stock_table(stock_results["results"])

    user_message = f"<query>{query}</query>\n<macro_context>{macro_context or 'NONE'}</macro_context>\n<stock_data>\n{stock_data or 'NONE'}\n</stock_data>"
    
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

def search_documents(query: str, filename: str = None, n_results: int = 10) -> list[dict]:
    """Raw vector search across documents, optionally filtered by filename."""
    return retrieve_macro(query, n_results=n_results, filename=filename)
