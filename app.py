import streamlit as st
import os
import datetime
from agent import analyze_layout_and_data, enrich_with_research
from renderer import ReportRenderer

st.set_page_config(page_title="Intelligent Internet | Report Gen", layout="wide", page_icon="🌐")

# --- BRANDED UI STYLES ---
st.markdown("""
<style>
    .stApp { background-color: #191e1b; color: white; }
    h1, h2, h3 { color: #bae9f4 !important; }
    .stTextInput input, .stTextArea textarea {
        background-color: #222825; border: 1px solid #56696d; color: white;
    }
    .stButton button {
        width: 100%; background: linear-gradient(90deg, #632af5 0%, #4f22c0 100%);
        color: white; border: none; padding: 12px 24px; border-radius: 30px;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("assets/logo.png"): st.image("assets/logo.png", width=80)
    st.header("Configuration")
    api_key = st.text_input("OpenAI API Key", type="password")
    if api_key: os.environ["OPENAI_API_KEY"] = api_key
    
    use_research = st.checkbox("Enable Live Research", help="Agent will search the web for citations.")

# --- MAIN ---
st.title("Institutional Report Generator")
st.markdown("Create **Intelligent Internet** strategy documents with dynamic layouts.")

col1, col2 = st.columns(2)
with col1:
    r_title = st.text_input("Title", "State of the Intelligent Internet")
    r_subtitle = st.text_input("Subtitle", "2025 Strategic Outlook")
with col2:
    r_date = st.text_input("Date", datetime.date.today().strftime("%B %d, %Y"))
    
summary = st.text_area("Executive Summary", "Enter summary...", height=80)
text_input = st.text_area("Content Body", "Paste raw text here...", height=300)

if st.button("Generate Report"):
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("Please enter API Key")
        st.stop()
        
    with st.status("🚀 Processing...", expanded=True) as status:
        
        # 1. Research
        content = text_input
        if use_research:
            status.write("🌍 Research Agent: Verifying facts...")
            content = enrich_with_research(content)
            
        # 2. Layout
        status.write("🧠 Design Agent: Structuring layouts...")
        layout_plan = analyze_layout_and_data(content)
        
        # 3. Render
        status.write("🎨 Composer: Generating PDF...")
        renderer = ReportRenderer()
        data = {
            "meta": {"title": r_title, "subtitle": r_subtitle, "date": r_date, "summary": summary},
            "sections": layout_plan.get('sections', [])
        }
        
        pdf = "Intelligent_Internet_Report.pdf"
        renderer.create_pdf(data, pdf)
        
        status.update(label="Done!", state="complete", expanded=False)
        
        with open(pdf, "rb") as f:
            st.download_button("📥 Download PDF", f, file_name=pdf)
