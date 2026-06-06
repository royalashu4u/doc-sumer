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
    /* Main Layout and Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Header Customization */
    .main-header {
        font-size: 2.6rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    .main-subtitle {
        font-size: 1.15rem;
        color: #94A3B8;
        margin-bottom: 1.8rem;
        font-weight: 400;
    }
    
    .checklist-item {
        color: #38BDF8;
        font-weight: 500;
        display: inline-block;
        margin-right: 15px;
    }
    
    /* Premium Content Cards Styling */
    .card {
        background-color: #1E293B;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.3);
        border: 1px solid #334155;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px -5px rgba(99, 102, 241, 0.15);
    }
    
    .card-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin-top: 0;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Segment-Specific Cards */
    .summary-card {
        border-left: 5px solid #6366F1; /* Indigo */
    }
    .summary-title {
        color: #818CF8;
    }
    
    .insights-card {
        border-left: 5px solid #10B981; /* Emerald */
    }
    .insights-title {
        color: #34D399;
    }
    
    .actions-card {
        border-left: 5px solid #8B5CF6; /* Violet */
    }
    .actions-title {
        color: #A78BFA;
    }
    
    .risks-card {
        border-left: 5px solid #F59E0B; /* Amber */
        background-color: #2D2316;
        border-color: #453015;
    }
    .risks-title {
        color: #FBBF24;
    }
    
    /* Bullet points styling */
    .bullet-list {
        list-style-type: none;
        padding-left: 0;
        margin: 0;
    }
    
    .bullet-list li {
        position: relative;
        padding-left: 30px;
        margin-bottom: 12px;
        font-size: 1.05rem;
        line-height: 1.5;
        color: #E2E8F0;
    }
    
    .bullet-list li::before {
        position: absolute;
        left: 0;
        top: 2px;
        font-weight: bold;
        font-size: 1.1rem;
    }
    
    .insights-list li::before {
        content: "✓";
        color: #10B981;
    }
    
    .actions-list li::before {
        content: "→";
        color: #8B5CF6;
    }
    
    .risks-list li::before {
        content: "⚠";
        color: #F59E0B;
    }
    
    /* Custom divider */
    .divider {
        height: 1px;
        background-color: #334155;
        margin: 20px 0;
    }
    
    /* Completely hide Streamlit sidebar controls to fix empty sidebar UI/UX */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    section[data-testid="stSidebar"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session States
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
    st.markdown("### ⚙️ Settings & Controls")
    
    # Language selector
    language = st.selectbox(
        "Output Language / अनुवाद",
        ["English", "Hindi"],
        index=0,
        help="Select the language for the final analysis."
    )
    
    # API key detection & Demo Toggle
    env_key = load_env_api_key()
    if env_key:
        st.markdown('<div style="color: #34D399; font-weight: 500; font-size: 0.95rem; margin-bottom: 8px;">⚡ Pollinations AI Connected</div>', unsafe_allow_html=True)
        is_demo_mode = st.toggle("🧪 Use Offline Demo Mode (Mock AI)", value=False)
    else:
        st.markdown('<div style="color: #FBBF24; font-weight: 500; font-size: 0.95rem; margin-bottom: 8px;">⚠️ Running in Offline Demo Mode (No API key found)</div>', unsafe_allow_html=True)
        is_demo_mode = True

    # Quick Demo Load Button
    load_demo_btn = st.button("📂 Load Demo Business PDF", use_container_width=True)

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

# Handle loading demo report PDF
if load_demo_btn:
    demo_path = "assets/demo_report.pdf"
    if os.path.exists(demo_path):
        with st.spinner("Loading demo document..."):
            try:
                extracted_text = extract_text(demo_path)
                st.session_state.pdf_text = extracted_text
                st.session_state.current_filename = "demo_report.pdf"
                st.session_state.summary_data = None
                st.session_state.processed = False
                st.session_state.chat_history = []
                st.success("Loaded demo_report.pdf successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error reading demo report: {str(e)}")
    else:
        st.error("Demo PDF file not found locally in `assets/` folder.")

# Clear status if no file is present and not loading demo
if uploaded_file is None and st.session_state.current_filename != "demo_report.pdf":
    st.session_state.pdf_text = None
    st.session_state.summary_data = None
    st.session_state.current_filename = None
    st.session_state.processed = False
    st.session_state.chat_history = []

# Display selected document info and analyze/chat split layout
if st.session_state.pdf_text:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Split the main interactive area into Left (Analysis/Controls) and Right (Chat)
    main_col_left, main_col_right = st.columns([5, 4], gap="large")
    
    with main_col_left:
        # Active document banner
        st.info(f"Active Document: **{st.session_state.current_filename}** ({len(st.session_state.pdf_text or '')} characters extracted)")
        
        # Analyze action button logic
        run_analysis = False
        if not st.session_state.processed or st.session_state.summary_data is None:
            button_label = "🚀 Run Document Analysis"
            if st.button(button_label, type="primary", use_container_width=True):
                run_analysis = True
        else:
            # Rerun triggers
            if "last_lang" in st.session_state and st.session_state.last_lang != language:
                run_analysis = True
            if "last_demo_mode" in st.session_state and st.session_state.last_demo_mode != is_demo_mode:
                run_analysis = True
                
        if run_analysis:
            with st.spinner("Analyzing document structure & generating insights..."):
                summary = get_ai_summary(
                    st.session_state.pdf_text,
                    api_key=env_key,
                    language=language,
                    is_demo=is_demo_mode
                )
                st.session_state.summary_data = summary
                st.session_state.last_lang = language
                st.session_state.last_demo_mode = is_demo_mode
                st.session_state.processed = True
                st.success("Analysis complete!")
                st.balloons()
                st.rerun() # rerun to render results immediately
                
        # Display Outputs (Only when processed)
        if st.session_state.processed and st.session_state.summary_data:
            summary_data = st.session_state.summary_data
            if "warning" in summary_data:
                st.warning(summary_data["warning"])
                
            # Executive Summary (Wide Card)
            exec_summary = summary_data.get("executive_summary", "No summary generated.")
            st.markdown(f"""
            <div class="card summary-card">
                <div class="card-title summary-title">📘 Executive Summary</div>
                <p style="font-size:1.1rem; line-height:1.6; color:#E2E8F0; margin:0;">{exec_summary}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Key Insights & Action Items inside left column stacked vertically for better readability
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
            
            # Risks/Caveats
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
            
            # Export
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            report_text = f"""==================================================
DOCUMENT ANALYSIS REPORT: {st.session_state.current_filename}
Language: {language}
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
            
        # Expander for raw text view (always useful for transparency/debugging)
        with st.expander("🔍 View Raw Extracted PDF Text"):
            st.text_area("Extracted Text Content", value=st.session_state.pdf_text, height=200, disabled=True)

    with main_col_right:
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

else:
    # Help guide when empty
    st.info("💡 Getting Started: Upload a PDF file using the uploader above, or click 'Load Demo Business PDF' in the settings panel to test immediately.")

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
