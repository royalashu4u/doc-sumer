import streamlit as st
import os
import time
from utils import extract_text, get_ai_summary, load_env_api_key

# 1. Page Configuration & Aesthetic Theme setup
st.set_page_config(
    page_title="AI Document Intelligence Assistant",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject custom premium CSS for visual excellence
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --primary-50: #EEF2FF;
        --primary-100: #E0E7FF;
        --primary-200: #C7D2FE;
        --primary-300: #A5B4FC;
        --primary-400: #818CF8;
        --primary-500: #6366F1;
        --primary-600: #4F46E5;
        --primary-700: #4338CA;
        --primary-800: #3730A3;
        --primary-900: #312E81;
        --surface-base: #0F1117;
        --surface-card: #181B23;
        --surface-elevated: #1E2230;
        --surface-hover: #262A3A;
        --border-subtle: rgba(255, 255, 255, 0.06);
        --border-default: rgba(255, 255, 255, 0.1);
        --border-accent: rgba(99, 102, 241, 0.3);
        --text-primary: #F1F5F9;
        --text-secondary: #94A3B8;
        --text-tertiary: #64748B;
        --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.4);
        --shadow-glow: 0 0 20px rgba(99, 102, 241, 0.15);
        --radius-sm: 6px;
        --radius-md: 10px;
        --radius-lg: 16px;
        --radius-xl: 20px;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: var(--surface-base);
        color: var(--text-primary);
    }

    .stApp {
        background: var(--surface-base);
    }

    /* ── Header ── */
    .main-header {
        font-size: clamp(1.8rem, 3.2vw, 3rem);
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #818CF8 0%, #A78BFA 40%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.15rem;
        line-height: 1.2;
    }

    .main-subtitle {
        font-size: clamp(0.95rem, 1.1vw, 1.1rem);
        color: var(--text-secondary);
        margin-bottom: 2rem;
        font-weight: 400;
        letter-spacing: -0.01em;
    }

    .checklist-item {
        color: var(--primary-400);
        font-weight: 500;
        display: inline-block;
        margin-right: 12px;
        background: rgba(99, 102, 241, 0.1);
        padding: 2px 10px;
        border-radius: var(--radius-sm);
        font-size: 0.85rem;
    }

    /* ── Cards ── */
    .card {
        background: var(--surface-card);
        border-radius: var(--radius-lg);
        padding: 20px 24px;
        margin-bottom: 16px;
        border: 1px solid var(--border-default);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .card:hover::before {
        opacity: 1;
    }

    .card:hover {
        transform: translateY(-1px);
        border-color: var(--border-accent);
        box-shadow: var(--shadow-lg), var(--shadow-glow);
    }

    .card-title {
        font-size: 1.05rem;
        font-weight: 600;
        letter-spacing: -0.01em;
        margin-top: 0;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .summary-card { border-left: 3px solid var(--primary-500); }
    .summary-title { color: var(--primary-400); }
    .insights-card { border-left: 3px solid #10B981; }
    .insights-title { color: #34D399; }
    .actions-card { border-left: 3px solid #8B5CF6; }
    .actions-title { color: #A78BFA; }
    .risks-card { border-left: 3px solid #F59E0B; }
    .risks-title { color: #FBBF24; }

    .card p {
        font-size: 0.95rem;
        line-height: 1.7;
        color: var(--text-secondary);
        margin: 0;
    }

    /* ── Bullet Lists ── */
    .bullet-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .bullet-list li {
        position: relative;
        padding: 8px 0 8px 28px;
        font-size: 0.9rem;
        line-height: 1.6;
        color: var(--text-secondary);
        border-bottom: 1px solid var(--border-subtle);
    }

    .bullet-list li:last-child {
        border-bottom: none;
    }

    .bullet-list li::before {
        position: absolute;
        left: 0;
        top: 9px;
        font-size: 0.8rem;
    }

    .insights-list li::before { content: "✓"; color: #10B981; }
    .actions-list li::before { content: "→"; color: #8B5CF6; }
    .risks-list li::before { content: "!"; color: #F59E0B; font-weight: 700; }

    /* ── Dividers ── */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, var(--border-default), transparent);
        margin: 24px 0;
    }

    /* ── Streamlit Overrides ── */
    [data-testid="collapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }

    .stTextInput, .stSelectbox, .stFileUploader {
        border-radius: var(--radius-md) !important;
    }

    div[data-testid="stFileUploader"] {
        background: var(--surface-card) !important;
        border: 1px dashed var(--border-default) !important;
        border-radius: var(--radius-lg) !important;
        padding: 16px !important;
        transition: border-color 0.2s ease;
    }

    div[data-testid="stFileUploader"]:hover {
        border-color: var(--primary-500) !important;
    }

    div[data-testid="stSelectbox"] > div {
        background: var(--surface-card) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: var(--radius-md) !important;
    }

    div[data-testid="stSelectbox"] > div:hover {
        border-color: var(--border-accent) !important;
    }

    .st-bb, .st-at, .st-ae, .st-ag {
        background-color: var(--surface-card) !important;
        color: var(--text-primary) !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: var(--radius-md) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.5rem 1.25rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        letter-spacing: -0.01em !important;
        border: 1px solid var(--border-default) !important;
        background: var(--surface-card) !important;
        color: var(--text-primary) !important;
    }

    .stButton > button:hover {
        border-color: var(--primary-500) !important;
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.15) !important;
        transform: translateY(-1px);
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary-600), var(--primary-700)) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 16px rgba(79, 70, 229, 0.3) !important;
    }

    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 24px rgba(79, 70, 229, 0.45) !important;
        transform: translateY(-2px);
    }

    /* Toggle */
    .stToggle > div[data-testid="stBaseWidget"] > label {
        gap: 8px !important;
    }

    .stToggle > div > div > div {
        background: var(--surface-hover) !important;
    }

    /* Info boxes */
    .stAlert {
        background: var(--surface-card) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-secondary) !important;
    }

    .stAlert > div:first-child {
        color: var(--primary-400) !important;
    }

    /* Chat messages */
    div[data-testid="stChatMessage"] {
        background: var(--surface-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
        padding: 12px 16px !important;
        margin-bottom: 8px !important;
    }

    div[data-testid="stChatMessage"][aria-label="user"] {
        border-left: 3px solid var(--primary-500) !important;
    }

    div[data-testid="stChatMessage"][aria-label="assistant"] {
        border-left: 3px solid #10B981 !important;
    }

    div[data-testid="stChatInput"] > div {
        background: var(--surface-card) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: var(--radius-lg) !important;
    }

    div[data-testid="stChatInput"] > div:focus-within {
        border-color: var(--primary-500) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #059669, #047857) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: var(--radius-md) !important;
        box-shadow: 0 4px 16px rgba(5, 150, 105, 0.3) !important;
    }

    .stDownloadButton > button:hover {
        box-shadow: 0 6px 24px rgba(5, 150, 105, 0.45) !important;
        transform: translateY(-2px);
    }

    /* Expander */
    .st-expander {
        background: var(--surface-card) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: var(--radius-md) !important;
    }

    .st-expander > div:first-child {
        background: transparent !important;
    }

    /* Spinner */
    .stSpinner > div > div {
        border-color: var(--primary-500) transparent transparent transparent !important;
    }

    .stSpinner p {
        color: var(--text-secondary) !important;
    }

    /* Success / Error / Warning messages */
    .stSuccess, .stError, .stWarning {
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--border-default) !important;
    }

    .stSuccess {
        background: rgba(16, 185, 129, 0.1) !important;
        border-color: rgba(16, 185, 129, 0.3) !important;
    }

    /* Language label */
    .lang-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 8px;
    }

    /* Balloons fix */
    .stBalloons {
        z-index: 9999 !important;
    }
</style>
""", unsafe_allow_html=True)

LANGUAGES = [
    "English", "Hindi", "Spanish", "French", "German", "Chinese",
    "Japanese", "Arabic", "Portuguese", "Russian", "Italian",
    "Dutch", "Korean", "Turkish", "Vietnamese", "Thai", "Indonesian",
    "Polish", "Swedish", "Greek", "Hebrew", "Romanian", "Ukrainian"
]

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = None
if "summary_data" not in st.session_state:
    st.session_state.summary_data = None
if "current_filename" not in st.session_state:
    st.session_state.current_filename = None
if "processed" not in st.session_state:
    st.session_state.processed = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "language" not in st.session_state:
    st.session_state.language = "English"

# 2. Main Screen Layout
# Dynamic Title
st.markdown('<div class="main-header">📄 AI Document Intelligence Assistant</div>', unsafe_allow_html=True)

# Subtitle checklist
st.markdown("""
<div class="main-subtitle">
    Upload a PDF and instantly extract intelligence:
    <span class="checklist-item">✓ Executive Summary</span>
    <span class="checklist-item">✓ Key Insights</span>
    <span class="checklist-item">✓ Action Items</span>
</div>
""", unsafe_allow_html=True)

# Language selector (global)
lang_col1, lang_col2, _ = st.columns([1, 2, 4])
with lang_col1:
    st.markdown("##### 🌐 Language")
with lang_col2:
    selected_lang = st.selectbox(
        "Language",
        LANGUAGES,
        index=LANGUAGES.index(st.session_state.language),
        label_visibility="collapsed"
    )
    st.session_state.language = selected_lang

# Main control panel layout (Upload file on the left, settings on the right)
col_upload, col_settings = st.columns([3, 2], gap="large")

with col_upload:
    st.markdown("### 📥 Document Upload")
    uploaded_file = st.file_uploader(
        "Upload PDF document to analyze",
        type=["pdf"],
        help="Drag and drop or browse to upload a PDF file"
    )

with col_settings:
    env_key = load_env_api_key()
    is_demo_mode = st.toggle("🧪 Use Offline Demo Mode (Mock AI)", value=not env_key)

    # Handle file upload change
if uploaded_file is not None:
    if st.session_state.current_filename != uploaded_file.name:
        # Reset if new file uploaded
        with st.spinner("Extracting text from uploaded PDF..."):
            try:
                extracted_text = extract_text(uploaded_file)
                st.session_state.pdf_text = extracted_text
                st.session_state.current_filename = uploaded_file.name
                st.session_state.summary_data = None
                st.session_state.processed = False
                st.session_state.chat_history = []
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Clear status if no file is present
if uploaded_file is None:
    st.session_state.pdf_text = None
    st.session_state.summary_data = None
    st.session_state.current_filename = None
    st.session_state.processed = False
    st.session_state.chat_history = []

# Display selected document info and analyze/chat split layout
if st.session_state.pdf_text:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Split the main interactive area — Chat on the left, Analysis on the right
    chat_col, analysis_col = st.columns([4, 5], gap="large")
    
    with chat_col:
        # Chat interface on the right side
        st.markdown('<div class="card summary-card" style="border-left-color: #8B5CF6;">'
                    '<div class="card-title" style="color: #C084FC; font-size: 1.25rem;">💬 Chat with Document</div>'
                    '<p style="font-size: 0.95rem; color: #94A3B8; margin: 0; line-height: 1.5;">'
                    'Ask questions, retrieve specific numbers, or query insights directly from this PDF document.'
                    '</p>'
                    '</div>', unsafe_allow_html=True)
        
        chat_container = st.container(height=520)
        
        with chat_container:
            if not st.session_state.chat_history:
                st.markdown(
                    '<div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; color: #64748B; font-style: italic; text-align: center; padding: 20px; margin-top: 150px;">'
                    '<span style="font-size: 2.5rem; margin-bottom: 15px;">🤖</span>'
                    'No messages yet.<br>Ask a question about the document below to begin.'
                    '</div>', 
                    unsafe_allow_html=True
                )
            else:
                for message in st.session_state.chat_history:
                    with st.chat_message(message["role"]):
                        st.write(message["content"])
                        
        if user_query := st.chat_input("Ask a question about the document...", key="chat_input_query"):
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            with chat_container:
                with st.chat_message("user"):
                    st.write(user_query)
            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("AI is looking through the document..."):
                        from utils import query_pdf_data
                        response_text = query_pdf_data(
                            text=st.session_state.pdf_text,
                            user_question=user_query,
                            history=st.session_state.chat_history[:-1],
                            api_key=env_key,
                            is_demo=is_demo_mode
                        )
                        st.write(response_text)
            st.session_state.chat_history.append({"role": "assistant", "content": response_text})
            st.rerun()

    with analysis_col:
        st.info(f"Active Document: **{st.session_state.current_filename}** ({len(st.session_state.pdf_text or '')} characters extracted)")

        run_analysis = False
        if not st.session_state.processed or st.session_state.summary_data is None:
            if st.button("🚀 Run Document Analysis", type="primary", use_container_width=True):
                run_analysis = True
        else:
            if "last_demo_mode" in st.session_state and st.session_state.last_demo_mode != is_demo_mode:
                run_analysis = True

        if run_analysis:
            with st.spinner("Analyzing document structure & generating insights..."):
                summary = get_ai_summary(
                    st.session_state.pdf_text,
                    api_key=env_key,
                    language=st.session_state.language,
                    is_demo=is_demo_mode
                )
                st.session_state.summary_data = summary
                st.session_state.last_demo_mode = is_demo_mode
                st.session_state.processed = True
                st.success("Analysis complete!")
                st.balloons()
                st.rerun()

        if st.session_state.processed and st.session_state.summary_data:
            summary_data = st.session_state.summary_data
            if "warning" in summary_data:
                st.warning(summary_data["warning"])

            exec_summary = summary_data.get("executive_summary", "No summary generated.")
            st.markdown(f"""
            <div class="card summary-card">
                <div class="card-title summary-title">📘 Executive Summary</div>
                <p style="font-size:1.1rem; line-height:1.6; color:#E2E8F0; margin:0;">{exec_summary}</p>
            </div>
            """, unsafe_allow_html=True)

            insights = summary_data.get("key_insights", [])
            insights_html = "".join([f"<li>{item}</li>" for item in insights])
            st.markdown(f"""
            <div class="card insights-card">
                <div class="card-title insights-title">⚡ Key Insights</div>
                <ul class="bullet-list insights-list">
                    {insights_html if insights_html else '<li>No insights extracted.</li>'}
                </ul>
            </div>
            """, unsafe_allow_html=True)

            actions = summary_data.get("action_items", [])
            actions_html = "".join([f"<li>{item}</li>" for item in actions])
            st.markdown(f"""
            <div class="card actions-card">
                <div class="card-title actions-title">🎯 Action Items</div>
                <ul class="bullet-list actions-list">
                    {actions_html if actions_html else '<li>No action items extracted.</li>'}
                </ul>
            </div>
            """, unsafe_allow_html=True)

            risks = summary_data.get("risks_notes", [])
            risks_html = "".join([f"<li>{item}</li>" for item in risks])
            st.markdown(f"""
            <div class="card risks-card">
                <div class="card-title risks-title">⚠️ Risks & Important Caveats</div>
                <ul class="bullet-list risks-list">
                    {risks_html if risks_html else '<li>No specific risks noted.</li>'}
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            report_text = f"""==================================================
DOCUMENT ANALYSIS REPORT: {st.session_state.current_filename}
Language: {st.session_state.language}
==================================================

EXECUTIVE SUMMARY:
{exec_summary}

KEY INSIGHTS:
"""
            for i, ins in enumerate(insights, 1):
                report_text += f" {i}. {ins}\n"
            report_text += "\nACTION ITEMS:\n"
            for i, act in enumerate(actions, 1):
                report_text += f" - {act}\n"
            report_text += "\nRISKS & NOTES:\n"
            for i, rsk in enumerate(risks, 1):
                report_text += f" * {rsk}\n"

            st.download_button(
                label="📥 Download Structured Report (.txt)",
                data=report_text,
                file_name=f"analysis_{st.session_state.current_filename.replace('.pdf', '')}.txt",
                mime="text/plain",
                use_container_width=True
            )

        with st.expander("🔍 View Raw Extracted PDF Text"):
            st.text_area("Extracted Text Content", value=st.session_state.pdf_text, height=200, disabled=True)

else:
    # Help guide when empty
    st.info("💡 Upload a PDF file using the uploader above to start analyzing your document.")

# Premium styled Pitch tip banner at the bottom
st.markdown("""
<div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%); 
            border: 1px solid rgba(99, 102, 241, 0.2); 
            border-radius: 12px; 
            padding: 16px; 
            margin-top: 40px; 
            text-align: center;">
    <span style="font-weight: 600; color: #818CF8; margin-right: 8px;">💡 Pitch tip:</span>
    <span style="color: #E2E8F0; font-style: italic;">
        Our AI Document Intelligence Assistant converts massive documents into precise, actionable structure, saving up to 80% of manual review time.
    </span>
</div>
""", unsafe_allow_html=True)
