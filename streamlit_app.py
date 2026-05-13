import streamlit as st
import requests

st.set_page_config(page_title="Stock Research Assistant", layout="wide", page_icon="📈")

def inject_custom_css():
    st.markdown("""
    <style>
    /* Gradient Background for App */
    .stApp {
        background: linear-gradient(-45deg, #0b0f19, #1a2a42, #29323c, #1a1a2e);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }
    
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Make Header Transparent */
    [data-testid="stHeader"] {
        background: rgba(0,0,0,0) !important;
    }

    /* Sidebar Glassmorphism */
    [data-testid="stSidebar"] {
        background: rgba(25, 30, 45, 0.4) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Chat Messages Glassmorphism */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Input Fields Glassmorphism */
    .stTextInput input, .stNumberInput input, .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 8px !important;
    }
    
    /* Chat Input Container */
    .stChatInputContainer {
        background: rgba(20, 25, 40, 0.6) !important;
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
    }

    /* Buttons Glassmorphism */
    .stButton > button {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #e0e0e0 !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.15) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        transform: translateY(-2px);
    }
    
    /* Primary Button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, rgba(74, 144, 226, 0.5), rgba(80, 227, 194, 0.5)) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
    }

    /* Expanders Glassmorphism */
    [data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
    }
    
    /* Tabs */
    [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 5px;
    }
    [data-baseweb="tab"] {
        background: transparent !important;
    }
    [aria-selected="true"] {
        background: rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }

    /* Metric Values */
    [data-testid="stMetricValue"] {
        color: #50e3c2 !important;
    }
    
    /* Fix text colors */
    .stMarkdown, .stText {
        color: rgba(255, 255, 255, 0.9) !important;
    }

    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ── helpers ──────────────────────────────────────────────────────────────────

def api(method: str, path: str, **kwargs):
    base = st.session_state.get("api_base_url", "http://localhost:8000")
    try:
        r = getattr(requests, method)(f"{base}{path}", timeout=120, **kwargs)
        return r
    except requests.exceptions.ConnectionError:
        return None


def fetch_documents() -> list[dict]:
    r = api("get", "/documents")
    if r and r.status_code == 200:
        return r.json().get("documents", [])
    return []


def badge(color: str, label: str) -> str:
    return f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75rem">{label}</span>'


# ── session defaults ──────────────────────────────────────────────────────────

for key, default in [
    ("api_base_url", "http://localhost:8000"),
    ("research_messages", []),
    ("search_messages", []),
    ("documents", None),          # cached doc list
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.title("⚙️ Configuration")
    new_url = st.text_input("API Base URL", value=st.session_state.api_base_url)
    if new_url != st.session_state.api_base_url:
        st.session_state.api_base_url = new_url
        st.session_state.documents = None   # reset cache on URL change

    # ── health indicator ────────────────────────────────────────────────────
    r = api("get", "/health")
    if r and r.status_code == 200:
        h = r.json()
        st.success(f"API online — LLM: `{h.get('llm_model','?')}` | Embed: `{h.get('embed_model','?')}`")
    else:
        st.error("API unreachable — is the FastAPI server running?")

    st.divider()

    # ── Knowledge Base panel ─────────────────────────────────────────────────
    st.subheader("📚 Knowledge Base")

    if st.button("🔄 Refresh document list", use_container_width=True):
        st.session_state.documents = None

    if st.session_state.documents is None:
        st.session_state.documents = fetch_documents()

    docs = st.session_state.documents
    if docs:
        total_chunks = sum(d["chunks"] for d in docs)
        st.caption(f"{len(docs)} documents · {total_chunks:,} chunks indexed")
        for doc in docs:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"📄 **{doc['filename']}**  \n`{doc['chunks']} chunks`")
            with col2:
                if st.button("🗑️", key=f"del_{doc['filename']}", help=f"Remove {doc['filename']} from index"):
                    r = api("delete", f"/documents/{doc['filename']}")
                    if r and r.status_code == 200:
                        st.success(f"Removed {doc['filename']}")
                        st.session_state.documents = None
                        st.rerun()
                    else:
                        detail = r.json().get("detail", "Unknown error") if r else "Connection error"
                        st.error(detail)
    else:
        st.info("No documents indexed yet.")

    st.divider()

    # ── Upload panel ─────────────────────────────────────────────────────────
    st.subheader("📁 Upload Data")

    with st.expander("📄 Upload Macro PDF", expanded=True):
        uploaded_pdf = st.file_uploader("Select PDF file", type=["pdf"], key="pdf_uploader")
        if uploaded_pdf:
            st.caption(f"Selected: **{uploaded_pdf.name}** ({uploaded_pdf.size / 1024:.1f} KB)")

            # Warn if already indexed
            already_indexed = any(d["filename"] == uploaded_pdf.name for d in (docs or []))
            if already_indexed:
                st.warning("⚠️ This document is already indexed. Uploading will replace it.")

            if st.button("⚡ Ingest PDF", use_container_width=True, type="primary"):
                with st.spinner(f"Embedding {uploaded_pdf.name} — this may take a minute..."):
                    files = {"file": (uploaded_pdf.name, uploaded_pdf.getvalue(), "application/pdf")}
                    r = api("post", "/upload/document", files=files)
                if r and r.status_code == 200:
                    data = r.json()
                    st.success(f"✅ Ingested **{data['filename']}** — {data.get('chunks_added', '?')} chunks added")
                    st.session_state.documents = None   # refresh list
                    st.rerun()
                else:
                    detail = r.json().get("detail", "Unknown error") if r else "Connection error"
                    st.error(f"Failed: {detail}")

    with st.expander("📊 Upload Stock CSV"):
        uploaded_csv = st.file_uploader("Select CSV file", type=["csv"], key="csv_uploader")
        if uploaded_csv:
            st.caption(f"Selected: **{uploaded_csv.name}** ({uploaded_csv.size / 1024:.1f} KB)")
            if st.button("⚡ Ingest CSV", use_container_width=True, type="primary"):
                with st.spinner("Loading stock data into database..."):
                    files = {"file": (uploaded_csv.name, uploaded_csv.getvalue(), "text/csv")}
                    r = api("post", "/upload/csv", files=files)
                if r and r.status_code == 200:
                    data = r.json()
                    st.success(f"✅ Ingested **{data['rows_ingested']:,} rows** from {uploaded_csv.name}")
                else:
                    detail = r.json().get("detail", "Unknown error") if r else "Connection error"
                    st.error(f"Failed: {detail}")


# ═════════════════════════════════════════════════════════════════════════════
# MAIN AREA
# ═════════════════════════════════════════════════════════════════════════════

st.title("📈 Stock Investment Research Assistant")
st.markdown("---")

tab_research, tab_search = st.tabs(["🤖 Research Assistant", "🔍 Document Search"])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — RESEARCH ASSISTANT (Synthesis)
# ─────────────────────────────────────────────────────────────────────────────

with tab_research:
    st.markdown(
        "Ask any question about stocks or the economy. "
        "The assistant combines structured stock data with macroeconomic documents to produce a synthesized answer."
    )

    # render history
    for msg in st.session_state.research_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "metadata" in msg:
                meta = msg["metadata"]
                cols = st.columns(3)
                cols[0].metric("Intent", meta.get("Intent", "—"))
                cols[1].metric("SQL used", "Yes" if meta.get("SQL Query") else "No")
                cols[2].metric("Doc sources", len(meta.get("Sources") or []))
                if meta.get("SQL Query") or meta.get("Sources"):
                    with st.expander("🔍 Full metadata"):
                        st.json(meta)

    prompt = st.chat_input("Ask a question about stocks or the economy…", key="research_input")
    if prompt:
        st.session_state.research_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Synthesizing answer from multiple sources…"):
                r = api("post", "/query", json={"question": prompt})

            if r and r.status_code == 200:
                data = r.json()
                answer = data.get("answer", "No answer returned.")
                st.markdown(answer)

                meta = {
                    "Intent": data.get("intent"),
                    "Sources": data.get("sources"),
                    "SQL Query": data.get("sql_used"),
                }
                cols = st.columns(3)
                cols[0].metric("Intent", meta["Intent"] or "—")
                cols[1].metric("SQL used", "Yes" if meta["SQL Query"] else "No")
                cols[2].metric("Doc sources", len(meta["Sources"] or []))
                if meta["SQL Query"] or meta["Sources"]:
                    with st.expander("🔍 Full metadata"):
                        st.json(meta)

                st.session_state.research_messages.append(
                    {"role": "assistant", "content": answer, "metadata": meta}
                )
            elif r and r.status_code == 422:
                st.error(f"Validation error: {r.json()}")
            else:
                st.error("API error or connection failure." if r is None else f"Error {r.status_code}: {r.text}")

    if st.session_state.research_messages and st.button("🗑️ Clear research history", key="clear_research"):
        st.session_state.research_messages = []
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — DOCUMENT SEARCH (Retrieval)
# ─────────────────────────────────────────────────────────────────────────────

with tab_search:
    st.markdown("Search the indexed PDF documents by keyword or phrase. Results are ranked by semantic similarity.")

    # ── Search controls ───────────────────────────────────────────────────────
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([3, 2, 1])

    with ctrl_col1:
        doc_names = ["All documents"] + [d["filename"] for d in (st.session_state.documents or [])]
        selected_doc = st.selectbox(
            "Filter by document",
            options=doc_names,
            index=0,
            help="Restrict search to a specific indexed PDF.",
        )
        filename_filter = None if selected_doc == "All documents" else selected_doc

    with ctrl_col2:
        search_criteria = st.selectbox(
            "Search type",
            options=["Semantic (meaning)", "Keyword boost (exact terms first)"],
            index=0,
            help="Semantic uses embedding similarity. Keyword boost prepends the query with 'exactly: ' to bias towards exact matches.",
        )

    with ctrl_col3:
        n_results = st.number_input("Max results", min_value=1, max_value=30, value=8, step=1)

    # ── render search history ────────────────────────────────────────────────
    for msg in st.session_state.search_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "results" in msg:
                for idx, r in enumerate(msg["results"]):
                    relevance = r.get("relevance")
                    rel_str = f"{relevance:.1f}%" if relevance is not None else "N/A"
                    color = "#2ecc71" if (relevance or 0) >= 60 else "#e67e22" if (relevance or 0) >= 35 else "#e74c3c"
                    with st.expander(
                        f"📄 {r['source']} — Page {r['page']}  |  Relevance: {rel_str}", expanded=(idx == 0)
                    ):
                        st.markdown(
                            f'<div style="border-left:4px solid {color};padding:8px 12px;'
                            f'background:#f8f9fa;border-radius:4px">{r["text"]}</div>',
                            unsafe_allow_html=True,
                        )

    # ── search input ─────────────────────────────────────────────────────────
    search_prompt = st.chat_input("Enter a keyword or phrase to search…", key="search_input")
    if search_prompt:
        display_query = search_prompt
        api_query = (
            f"exactly: {search_prompt}"
            if search_criteria == "Keyword boost (exact terms first)"
            else search_prompt
        )

        user_note = f"**Search:** {display_query}"
        if filename_filter:
            user_note += f"  \n**Filter:** `{filename_filter}`"
        user_note += f"  \n**Type:** {search_criteria} · **Max results:** {n_results}"

        st.session_state.search_messages.append({"role": "user", "content": user_note})
        with st.chat_message("user"):
            st.markdown(user_note)

        with st.chat_message("assistant"):
            with st.spinner("Searching document index…"):
                payload = {"query": api_query, "n_results": int(n_results)}
                if filename_filter:
                    payload["filename"] = filename_filter
                r = api("post", "/search", json=payload)

            if r and r.status_code == 200:
                data = r.json()
                results = data.get("results", [])

                if not results:
                    msg_text = f"No matching snippets found for **{display_query}**."
                    if filename_filter:
                        msg_text += f" Try removing the document filter."
                    st.warning(msg_text)
                    st.session_state.search_messages.append({"role": "assistant", "content": msg_text})
                else:
                    # Summary line
                    sources_found = sorted({res["source"] for res in results})
                    summary = (
                        f"Found **{len(results)} snippet{'s' if len(results) != 1 else ''}** "
                        f"across **{len(sources_found)} document{'s' if len(sources_found) != 1 else ''}**."
                    )
                    st.markdown(summary)

                    # Inline snippet cards
                    for idx, res in enumerate(results):
                        relevance = res.get("relevance")
                        rel_str = f"{relevance:.1f}%" if relevance is not None else "N/A"
                        color = (
                            "#2ecc71" if (relevance or 0) >= 60
                            else "#e67e22" if (relevance or 0) >= 35
                            else "#e74c3c"
                        )
                        with st.expander(
                            f"📄 {res['source']} — Page {res['page']}  |  Relevance: {rel_str}",
                            expanded=(idx == 0),
                        ):
                            st.markdown(
                                f'<div style="border-left:4px solid {color};padding:8px 12px;'
                                f'background:#f8f9fa;border-radius:4px">{res["text"]}</div>',
                                unsafe_allow_html=True,
                            )

                    st.session_state.search_messages.append(
                        {"role": "assistant", "content": summary, "results": results}
                    )

            elif r and r.status_code == 422:
                st.error(f"Validation error: {r.json()}")
            else:
                st.error("API error or connection failure." if r is None else f"Error {r.status_code}: {r.text}")

    if st.session_state.search_messages and st.button("🗑️ Clear search history", key="clear_search"):
        st.session_state.search_messages = []
        st.rerun()
