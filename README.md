# 📊 Stock Research Assistance Project

GenAI-powered assistant capable of answering user queries by combining information from:
- Unstructured data: A collection of macroeconomic and strategic documents (PDFs).
- Structured data: A CSV file containing stock information (e.g., prices, P/E ratios, market caps, etc.).

## 💡 Prerequisites
- Install Ollama: https://ollama.com

## 🔥 Here we use following models

Pull models:
```bash
ollama pull gemma4
ollama pull qwen3-embedding
```

## 🛡️ Setup the project

Create a virtual environment and activate it
```bash
# For Mac
python3.11 -m venv myenv
source myenv/bin/activate

# For Windows
python -m venv myenv
myenv\Scripts\activate
```

Install dependencies
```bash
pip install -r requirements.txt
```

## 🎯 Ingest data
Create a folder in the project root. Name it data, then create another folder called pdfs.
Provide your PDFs in `data/pdfs/` and your stock data in `data/stocks.csv`, then run:
```bash
python3.11 -m ingest.pdf_ingestor ./data/pdfs/
python3.11 -m ingest.csv_ingestor ./data/stocks.csv
```

## 🚀 Run backend
This project uses FastAPI, therefore from the terminal run the following command.

Launch the server:
```bash
uvicorn main:app --reload
```
The API will be available at `http://localhost:8000/docs`.

## 🚀 Run the Frontend
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

## 🐛 Example queries (curl)
### 🌐 Stock only
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Which technology stocks have a dividend yield above 2%? "}'
```

### 🌐 Stock only
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is stock price for AAPL"}'
```

### 🌐 Macro only  
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the key macroeconomic risks for 2024?"}'
```

### 🌐 Hybrid
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Teslas target price and how does the macro environment affect it?"}'
```

### 🌐 Search documents
```bash 
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "interest rates"}'
```

### 🌐 Search documents with filename filter
```bash 
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "interest rates", "filename": "example.pdf"}'
```

## 📖 Assumptions & Limitations
- Ollama must be running locally before starting the server
- Embedding quality depends on qwen3-embedding; swap to a larger model for better recall
- gemma4 Text-to-SQL accuracy is good for simple queries;
- ChromaDB and SQLite are stored locally — not suitable for multi-user production deployments

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔒 Security
For security concerns, please review our [Security Policy](SECURITY.md).
