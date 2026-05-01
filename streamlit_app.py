import streamlit as st
import requests
import json

# App configuration
st.set_page_config(page_title="Stock Research Assistant", layout="wide", page_icon="📈")

# Sidebar - Configuration and Ingestion
st.sidebar.title("⚙️ Configuration")
api_base_url = st.sidebar.text_input("API Base URL", value="http://localhost:8000")

st.sidebar.divider()

st.sidebar.title("📁 Data Ingestion")
st.sidebar.info("Upload new documents or stock data to expand the knowledge base.")

# PDF Upload
uploaded_pdf = st.sidebar.file_uploader("Upload Macro PDF", type=["pdf"])
if uploaded_pdf:
    if st.sidebar.button("Ingest PDF", use_container_width=True):
        with st.spinner("Extracting and embedding PDF..."):
            try:
                files = {"file": (uploaded_pdf.name, uploaded_pdf.getvalue(), "application/pdf")}
                response = requests.post(f"{api_base_url}/upload/document", files=files)
                if response.status_code == 200:
                    st.sidebar.success(f"Successfully ingested: {uploaded_pdf.name}")
                else:
                    st.sidebar.error(f"Failed: {response.json().get('detail', 'Unknown error')}")
            except Exception as e:
                st.sidebar.error(f"Connection error: {e}")

# CSV Upload
uploaded_csv = st.sidebar.file_uploader("Upload Stock CSV", type=["csv"])
if uploaded_csv:
    if st.sidebar.button("Ingest CSV", use_container_width=True):
        with st.spinner("Processing stock data..."):
            try:
                files = {"file": (uploaded_csv.name, uploaded_csv.getvalue(), "text/csv")}
                response = requests.post(f"{api_base_url}/upload/csv", files=files)
                if response.status_code == 200:
                    data = response.json()
                    st.sidebar.success(f"Ingested {data['rows_ingested']} rows from {uploaded_csv.name}")
                else:
                    st.sidebar.error(f"Failed: {response.json().get('detail', 'Unknown error')}")
            except Exception as e:
                st.sidebar.error(f"Connection error: {e}")

# Main UI
st.title("📈 Stock Investment Research Assistant")
st.markdown("---")

# Mode Selection
mode = st.radio(
    "Choose Interaction Mode:",
    ["Research Assistant (Synthesis)", "Document Search (Retrieval)"],
    index=0,
    horizontal=True,
    help="Assistant: Synthesizes an answer from all sources. Search: Returns raw snippets from PDFs."
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "metadata" in message:
            with st.expander("🔍 Analysis Metadata"):
                st.json(message["metadata"])
        if "results" in message:
            with st.expander("📄 Document Snippets"):
                for r in message["results"]:
                    st.markdown(f"**Source**: `{r['source']}` (Page {r['page']})")
                    st.caption(r['text'])
                    st.divider()

# Chat input
if prompt := st.chat_input("Ask a question about stocks or the economy..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response
    with st.chat_message("assistant"):
        if mode == "Research Assistant (Synthesis)":
            with st.spinner("Synthesizing answer from multiple sources..."):
                try:
                    response = requests.post(f"{api_base_url}/query", json={"question": prompt})
                    if response.status_code == 200:
                        data = response.json()
                        answer = data["answer"]
                        st.markdown(answer)
                        
                        metadata = {
                            "Intent": data.get("intent"),
                            "Sources": data.get("sources"),
                            "SQL Query": data.get("sql_used")
                        }
                        st.session_state.messages.append({"role": "assistant", "content": answer, "metadata": metadata})
                        with st.expander("🔍 Analysis Metadata"):
                            st.json(metadata)
                    else:
                        error_msg = f"API Error ({response.status_code}): {response.text}"
                        st.error(error_msg)
                except Exception as e:
                    st.error(f"Connection failure: {e}")
        
        else:
            # Search mode
            with st.spinner("Searching document index..."):
                try:
                    response = requests.post(f"{api_base_url}/search", json={"query": prompt})
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("results", [])
                        
                        if not results:
                            answer = "No matching snippets found."
                            st.warning(answer)
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                        else:
                            answer = f"Found {len(results)} relevant snippets in the documents."
                            st.markdown(answer)
                            st.session_state.messages.append({"role": "assistant", "content": answer, "results": results})
                            with st.expander("📄 Document Snippets"):
                                for r in results:
                                    st.markdown(f"**Source**: `{r['source']}` (Page {r['page']})")
                                    st.caption(r['text'])
                                    st.divider()
                    else:
                        st.error(f"API Error: {response.status_code}")
                except Exception as e:
                    st.error(f"Connection failure: {e}")
