# Stock Investment Research Assistant

A fully local AI-powered REST API 0using Ollama.


## Prerequisites
- Install Ollama: https://ollama.com


## Here we use following models

Pull models:
```bash
ollama pull gemma4
ollama pull qwen3-embedding
```


## Setup

Create a virtual environment and activate it
```bash
For Mac
python3.11 -m venv myenv
source myenv/bin/activate

For windows
python -m venv myenv
myenv/Scripts/activate
```

Install dependencies
```bash
pip install -r requirements.txt
```

## Ingest data
Provide your PDFs in `data/pdfs/` and your stock data in `data/stocks.csv`, then run:
```bash
python3.11 -m ingest.pdf_ingestor ./data/pdfs/
python3.11 -m ingest.csv_ingestor ./data/stocks.csv
```

## Run
```bash
uvicorn main:app --reload
```

## Example queries (curl)
### Stock only
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Which technology stocks have a dividend yield above 2%? "}'
```

### Stock only
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is stock price for AAPL"}'
```

### Macro only  
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the key macroeconomic risks for 2024?"}'
```

### Hybrid
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Teslas target price and how does the macro environment affect it?"}'
```
### Search documents
```bash 
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "interest rates"}'
```

### Search documents with filename filter
```bash 
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "interest rates", "filename": "example.pdf"}'
```


## Running the Frontend
The project includes a Streamlit-based user interface for easier interaction.

1. Activate the virtual environment:
    ```bash
    source myenv/bin/activate
    ```
2. Launch the Streamlit app:
    ```bash
    streamlit run streamlit_app.py
    ```

The app will be available at `http://localhost:8501`.

## Assumptions & Limitations
- Ollama must be running locally before starting the server
- Embedding quality depends on qwen3-embedding; swap to a larger model for better recall
- gemma4 Text-to-SQL accuracy is good for simple queries;
- ChromaDB and SQLite are stored locally — not suitable for multi-user production deployments
