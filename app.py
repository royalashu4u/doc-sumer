import streamlit as st
from utils import extract_text, get_ai_summary, load_env_api_key

st.set_page_config(
    page_title="Document Intelligence",
    page_icon="▣",
    layout="wide",
    initial_sidebar_state="collapsed"
)

LANGUAGES = [
    "English", "Hindi", "Spanish", "French", "German", "Chinese",
    "Japanese", "Arabic", "Portuguese", "Russian", "Italian",
    "Dutch", "Korean", "Turkish", "Vietnamese", "Thai", "Indonesian",
    "Polish", "Swedish", "Greek", "Hebrew", "Romanian", "Ukrainian"
]

for key in ["pdf_text", "summary_data", "current_filename", "chat_history", "language", "processing"]:
    if key not in st.session_state:
        if key == "language":
            st.session_state[key] = "English"
        elif key == "processing":
            st.session_state[key] = False
        elif key == "chat_history":
            st.session_state[key] = []
        else:
            st.session_state[key] = None

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root {
        --bg: #09090B;
        --surface: #111113;
        --surface-elevated: #18181B;
        --border: rgba(255,255,255,0.08);
        --primary: #7C3AED;
        --primary-hover: #8B5CF6;
        --primary-glow: rgba(124,58,237,0.2);
        --success: #22C55E;
        --warning: #F59E0B;
        --text: #FAFAFA;
        --muted: #A1A1AA;
        --radius: 10px;
    }

    html, body, .stApp { background: var(--bg); font-family: 'Inter', sans-serif; color: var(--text); }

    /* ── Typography ── */
    .hero-icon {
        width: 52px; height: 52px;
        background: linear-gradient(135deg, var(--primary), #A855F7);
        border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.5rem; margin: 0 auto 20px;
        box-shadow: 0 8px 32px var(--primary-glow);
    }
    .hero-title {
        font-size: clamp(2rem, 4vw, 3.2rem); font-weight: 800;
        letter-spacing: -0.03em; line-height: 1.15;
        background: linear-gradient(135deg, #FAFAFA 0%, #A1A1AA 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; margin-bottom: 8px;
    }
    .hero-sub {
        font-size: 1.05rem; color: var(--muted); font-weight: 400;
        margin-bottom: 32px; line-height: 1.5;
    }

    .section-title {
        font-size: 1.1rem; font-weight: 600;
        color: var(--text); letter-spacing: -0.01em;
        margin-bottom: 4px;
    }
    .section-sub {
        font-size: 0.85rem; color: var(--muted); margin-bottom: 20px;
    }

    /* ── Upload Zone ── */
    div[data-testid="stFileUploader"] {
        background: var(--surface) !important;
        border: 1.5px dashed rgba(255,255,255,0.1) !important;
        border-radius: 16px !important;
        padding: 48px 24px !important;
        transition: all 0.3s ease;
        text-align: center;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: var(--primary) !important;
        background: rgba(124,58,237,0.03) !important;
    }
    div[data-testid="stFileUploader"] > div:first-child {
        display: flex; flex-direction: column; align-items: center; gap: 8px;
    }
    div[data-testid="stFileUploader"] small {
        color: var(--muted) !important; font-size: 0.85rem !important;
    }

    /* ── Cards ── */
    .card {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius); padding: 20px 24px; margin-bottom: 12px;
    }
    .card-header {
        display: flex; align-items: center; gap: 10px;
        font-size: 0.95rem; font-weight: 600; color: var(--text);
        padding-bottom: 14px; border-bottom: 1px solid var(--border);
        margin-bottom: 14px;
    }
    .card-header-icon {
        width: 28px; height: 28px; border-radius: 7px;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.85rem; flex-shrink: 0;
    }
    .card p { font-size: 0.9rem; line-height: 1.7; color: var(--muted); margin: 0; }

    /* ── List Items ── */
    .list-item {
        display: flex; align-items: flex-start; gap: 12px;
        padding: 10px 0; border-bottom: 1px solid var(--border);
        font-size: 0.9rem; line-height: 1.5; color: var(--muted);
    }
    .list-item:last-child { border-bottom: none; }
    .list-dot {
        width: 6px; height: 6px; border-radius: 50%;
        margin-top: 8px; flex-shrink: 0;
    }

    /* ── Doc Bar ── */
    .doc-bar {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius); padding: 14px 20px;
        display: flex; align-items: center; justify-content: space-between;
        margin-bottom: 24px;
    }
    .doc-bar-left { display: flex; align-items: center; gap: 12px; }
    .doc-icon {
        width: 36px; height: 36px; background: rgba(124,58,237,0.12);
        border-radius: 8px; display: flex; align-items: center; justify-content: center;
        font-size: 1rem;
    }
    .doc-name { font-size: 0.9rem; font-weight: 500; color: var(--text); }
    .doc-meta { font-size: 0.8rem; color: var(--muted); }
    .doc-badge {
        font-size: 0.75rem; padding: 3px 10px; border-radius: 100px;
        font-weight: 500;
    }
    .badge-ready { background: rgba(34,197,94,0.12); color: var(--success); }
    .badge-pending { background: rgba(245,158,11,0.12); color: var(--warning); }

    /* ── Processing Steps ── */
    .step-row {
        display: flex; align-items: center; gap: 14px; padding: 8px 0;
        font-size: 0.9rem; color: var(--muted);
    }
    .step-indicator {
        width: 24px; height: 24px; border-radius: 50%; flex-shrink: 0;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.7rem; font-weight: 600;
    }
    .step-done { background: rgba(34,197,94,0.15); color: var(--success); }
    .step-active { background: rgba(124,58,237,0.15); color: var(--primary); }
    .step-pending { background: rgba(255,255,255,0.05); color: #3F3F46; }

    /* ── Chat ── */
    .prompt-chip {
        display: inline-block; font-size: 0.8rem; color: var(--muted);
        background: var(--surface-elevated); border: 1px solid var(--border);
        border-radius: 100px; padding: 5px 14px; margin: 0 6px 8px 0;
        cursor: pointer; transition: all 0.2s;
    }
    .prompt-chip:hover { border-color: var(--primary); color: var(--text); }

    /* ── Buttons ── */
    .stButton > button {
        border-radius: var(--radius) !important;
        font-weight: 600 !important; font-size: 0.88rem !important;
        transition: all 0.2s ease !important;
        border: 1px solid var(--border) !important;
        background: var(--surface) !important;
        color: var(--text) !important;
        height: auto !important; padding: 0.5rem 1.25rem !important;
    }
    .stButton > button:hover {
        border-color: var(--primary) !important;
        box-shadow: 0 0 24px var(--primary-glow) !important;
    }
    .stButton > button[kind="primary"] {
        background: var(--primary) !important; border: none !important;
        color: white !important;
        box-shadow: 0 4px 20px var(--primary-glow) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--primary-hover) !important;
        box-shadow: 0 6px 28px var(--primary-glow) !important;
    }

    .stDownloadButton > button {
        background: var(--surface-elevated) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important; font-weight: 500 !important;
        border-radius: var(--radius) !important;
    }
    .stDownloadButton > button:hover {
        border-color: var(--primary) !important;
    }

    /* ── Streamlit Overrides ── */
    [data-testid="collapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }

    div[data-testid="stSelectbox"] > div {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
    }

    .st-bb, .st-at, .st-ae, .st-ag { background: var(--surface) !important; color: var(--text) !important; }

    div[data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        padding: 8px 0 !important;
    }
    div[data-testid="stChatMessageContent"] {
        font-size: 0.9rem !important; color: var(--muted) !important;
    }
    div[data-testid="stChatInput"] > div {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
    }
    div[data-testid="stChatInput"] > div:focus-within {
        border-color: var(--primary) !important;
    }

    .stAlert {
        background: transparent !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        color: var(--muted) !important;
    }
    .stSpinner > div > div { border-color: var(--primary) transparent transparent transparent !important; }
    .stSpinner p { color: var(--muted) !important; }
    .stSuccess { background: rgba(34,197,94,0.06) !important; border-color: rgba(34,197,94,0.2) !important; }
    .stBalloons { z-index: 9999 !important; }

    .block-container {
        max-width: 900px !important;
        padding-top: 2rem !important;
    }

    /* ── Divider ── */
    .sep {
        height: 1px; background: var(--border); margin: 28px 0;
    }

    /* ── Empty state centered ── */
    .empty-wrap {
        display: flex; flex-direction: column; align-items: center;
        padding: 60px 0 40px; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

env_key = load_env_api_key()

# ─────────────────────────────────────────────
# HERO — Empty state
# ─────────────────────────────────────────────
if not st.session_state.pdf_text:
    st.markdown('<div class="empty-wrap">', unsafe_allow_html=True)
    st.markdown("""<div class="hero-icon">▣</div>""", unsafe_allow_html=True)
    st.markdown("""<div class="hero-title">Document Intelligence</div>""", unsafe_allow_html=True)
    st.markdown("""<div class="hero-sub">Transform documents into decisions.</div>""", unsafe_allow_html=True)

    lang_a, lang_b = st.columns([3, 2])
    with lang_b:
        selected_lang = st.selectbox(
            "Language",
            LANGUAGES,
            index=LANGUAGES.index(st.session_state.language),
            label_visibility="collapsed"
        )
        st.session_state.language = selected_lang

    uploaded_file = st.file_uploader(
        "Upload a PDF document",
        type=["pdf"],
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        with st.spinner("Extracting text..."):
            st.session_state.pdf_text = extract_text(uploaded_file)
            st.session_state.current_filename = uploaded_file.name
            st.session_state.summary_data = None
            st.session_state.processing = False
            st.session_state.chat_history = []
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────
# DOCUMENT LOADED — Processing & Results
# ─────────────────────────────────────────────

# Document Bar
status_badge = '<span class="doc-badge badge-pending">Pending</span>' if not st.session_state.processed else '<span class="doc-badge badge-ready">Analyzed</span>'
st.markdown(f"""
<div class="doc-bar">
    <div class="doc-bar-left">
        <div class="doc-icon">▣</div>
        <div>
            <div class="doc-name">{st.session_state.current_filename}</div>
            <div class="doc-meta">{len(st.session_state.pdf_text or '')} chars extracted · {st.session_state.language}</div>
        </div>
    </div>
    {status_badge}
</div>
""", unsafe_allow_html=True)

# Analysis trigger
if not st.session_state.processed:
    col_a, col_b, _ = st.columns([2, 2, 4])
    with col_a:
        selected_lang = st.selectbox(
            "Language",
            LANGUAGES,
            index=LANGUAGES.index(st.session_state.language),
            label_visibility="collapsed"
        )
        st.session_state.language = selected_lang
    with col_b:
        analyze = st.button("Analyze Document", type="primary", use_container_width=True)

    if analyze:
        st.session_state.processing = True
        step_placeholder = st.empty()

        with step_placeholder:
            st.markdown("<div style='margin: 24px 0 8px;'>", unsafe_allow_html=True)
            steps = [
                ("▣", "Extracting document structure", "step-active"),
                ("◆", "Analyzing content", "step-pending"),
                ("◉", "Generating insights", "step-pending"),
            ]
            for icon, label, state in steps:
                st.markdown(f"""<div class="step-row"><div class="step-indicator {state}">{icon}</div>{label}</div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        summary = get_ai_summary(
            st.session_state.pdf_text,
            api_key=env_key,
            language=st.session_state.language
        )
        st.session_state.summary_data = summary
        st.session_state.processed = True
        st.session_state.processing = False
        step_placeholder.empty()
        st.rerun()

    col_x, _ = st.columns([1, 5])
    with col_x:
        if st.button("← Back"):
            st.session_state.pdf_text = None
            st.session_state.summary_data = None
            st.session_state.current_filename = None
            st.session_state.processed = False
            st.session_state.chat_history = []
            st.rerun()

else:
    # ── RESULTS ──
    data = st.session_state.summary_data
    if not data:
        st.warning("No analysis data found. Please re-analyze.")

    else:
        # Executive Summary
        exec_summary = data.get("executive_summary", "")
        st.markdown(f"""
        <div class="card">
            <div class="card-header">
                <div class="card-header-icon" style="background:rgba(124,58,237,0.12);color:#A78BFA;">▣</div>
                Executive Summary
            </div>
            <p>{exec_summary}</p>
        </div>
        """, unsafe_allow_html=True)

        # Key Insights
        insights = data.get("key_insights", [])
        if insights:
            items = "".join(f'<div class="list-item"><div class="list-dot" style="background:#22C55E;"></div>{i}</div>' for i in insights)
            st.markdown(f"""
            <div class="card">
                <div class="card-header">
                    <div class="card-header-icon" style="background:rgba(34,197,94,0.12);color:#22C55E;">⚡</div>
                    Key Insights
                </div>
                {items}
            </div>
            """, unsafe_allow_html=True)

        # Action Items
        actions = data.get("action_items", [])
        if actions:
            items = "".join(f'<div class="list-item"><div class="list-dot" style="background:#7C3AED;"></div>{a}</div>' for a in actions)
            st.markdown(f"""
            <div class="card">
                <div class="card-header">
                    <div class="card-header-icon" style="background:rgba(124,58,237,0.12);color:#A78BFA;">◆</div>
                    Action Items
                </div>
                {items}
            </div>
            """, unsafe_allow_html=True)

        # Risks
        risks = data.get("risks_notes", [])
        if risks:
            items = "".join(f'<div class="list-item"><div class="list-dot" style="background:#F59E0B;"></div>{r}</div>' for r in risks)
            st.markdown(f"""
            <div class="card">
                <div class="card-header">
                    <div class="card-header-icon" style="background:rgba(245,158,11,0.12);color:#FBBF24;">!</div>
                    Risk Assessment
                </div>
                {items}
            </div>
            """, unsafe_allow_html=True)

        # Export + Back
        e1, e2, _ = st.columns([2, 2, 4])
        with e1:
            report_text = f"""DOCUMENT ANALYSIS
File: {st.session_state.current_filename}
Language: {st.session_state.language}

EXECUTIVE SUMMARY:
{exec_summary}

KEY INSIGHTS:
""" + "\n".join(f" • {i}" for i in insights) + "\n\nACTION ITEMS:\n" + "\n".join(f" → {a}" for a in actions) + "\n\nRISKS:\n" + "\n".join(f" ! {r}" for r in risks)

            st.download_button(
                label="Export Report",
                data=report_text,
                file_name=f"report_{st.session_state.current_filename.replace('.pdf','')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with e2:
            if st.button("← New Document", use_container_width=True):
                st.session_state.pdf_text = None
                st.session_state.summary_data = None
                st.session_state.current_filename = None
                st.session_state.processed = False
                st.session_state.chat_history = []
                st.rerun()

        # Raw text expander
        with st.expander("View raw extracted text"):
            st.text_area("", value=st.session_state.pdf_text, height=150, disabled=True, label_visibility="collapsed")

    # ── CHAT ──
    st.markdown('<div class="sep"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Ask anything about this document</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Get answers based on the document content.</div>', unsafe_allow_html=True)

    if not st.session_state.chat_history:
        chips = ["Summarize financial risks", "Show largest transactions", "Find deadlines", "Extract key numbers", "Compare with previous"]
        chip_row = "".join(f'<span class="prompt-chip">{c}</span>' for c in chips)
        st.markdown(f"<div style='margin-bottom:16px;'>{chip_row}</div>", unsafe_allow_html=True)

    chat_container = st.container(height=360)

    with chat_container:
        if not st.session_state.chat_history:
            st.markdown(
                '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:#3F3F46;text-align:center;padding:20px;">'
                '<span style="font-size:2rem;margin-bottom:12px;">💬</span>'
                'Ask a question to get started.</div>',
                unsafe_allow_html=True
            )
        else:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    if user_query := st.chat_input("Ask anything about this document..."):
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_query)
            with st.chat_message("assistant"):
                with st.spinner(""):
                    from utils import query_pdf_data
                    response_text = query_pdf_data(
                        text=st.session_state.pdf_text,
                        user_question=user_query,
                        history=st.session_state.chat_history[:-1],
                        api_key=env_key
                    )
                    st.markdown(response_text)
        st.session_state.chat_history.append({"role": "assistant", "content": response_text})
        st.rerun()
