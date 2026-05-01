import os
import glob
from pypdf import PdfReader
import ollama
import chromadb

from config import EMBED_MODEL, CHROMA_PATH, COLLECTION_NAME, OLLAMA_BASE_URL

# Set Ollama host from config
os.environ["OLLAMA_HOST"] = OLLAMA_BASE_URL

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def ingest_pdf(pdf_path: str):
    print(f"Ingesting {pdf_path}...")
    reader = PdfReader(pdf_path)
    filename = os.path.basename(pdf_path)
    
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text:
            continue
            
        chunks = chunk_text(text)
        
        for j, chunk in enumerate(chunks):
            try:
                response = ollama.embeddings(model=EMBED_MODEL, prompt=chunk)
                embedding = response["embedding"]
                
                doc_id = f"{filename}_p{i+1}_{j}"
                
                collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{"source": filename, "page": i + 1}]
                )
            except Exception as e:
                print(f"Error embedding chunk {j} of page {i+1} in {filename}: {e}")

def ingest_folder(folder_path: str):
    pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
    for pdf_path in pdf_files:
        ingest_pdf(pdf_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        folder_to_ingest = sys.argv[1]
        ingest_folder(folder_to_ingest)
    else:
        print("Usage: python -m ingest.pdf_ingestor <folder_path>")
