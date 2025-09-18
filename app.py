# app.py
import streamlit as st
from resume_parser import extract_text
from job_matcher import extract_keywords, match_score
from ai_feedback import generate_resume_feedback, rewrite_section
from io import BytesIO
from docx import Document
import os

st.set_page_config(page_title="Smart Resume Analyzer", page_icon="📄")
st.title("📄 Smart Resume Analyzer — Local (MVP)")

st.sidebar.header("Settings")
model_choice = st.sidebar.selectbox("OpenAI model", ["(use .env) gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"], index=0)
st.sidebar.write("If you want to force a model, pick it above. Otherwise set OPENAI_MODEL in .env or env.")

uploaded_file = st.file_uploader("Upload resume (PDF/DOCX/TXT)")
job_desc = st.text_area("Paste job description", height=200)

if uploaded_file and job_desc.strip():
    with st.spinner("Extracting text..."):
        resume_text = extract_text(uploaded_file)
    st.subheader("Resume preview (first 1000 chars)")
    st.code(resume_text[:1000] + ("..." if len(resume_text) > 1000 else ""))

    job_keywords = extract_keywords(job_desc, top_n=50)
    score_data = match_score(resume_text, job_keywords)
    st.metric("Match Score", f"{score_data['score']}%")
    st.write("Missing keywords (top 20):")
    st.write(", ".join(score_data["missing"][:20]) or "None detected")

    force_model = None
    if model_choice != "(use .env) gpt-4o-mini":
        force_model = model_choice

    if st.button("Generate AI suggestions"):
        st.info("Generating suggestions (OpenAI request)...")
        try:
            feedback = generate_resume_feedback(resume_text, job_desc, match_data=score_data, model_choice=force_model)
            if "raw" in feedback:
                st.warning("Model returned free text (not JSON). Showing raw output.")
                st.write(feedback["raw"])
            else:
                st.success("AI suggestions ready")
                st.subheader("Summary")
                st.write(feedback.get("summary", ""))
                st.subheader("Top Improvements")
                for i, it in enumerate(feedback.get("top_improvements", [])[:10], 1):
                    st.write(f"{i}. {it}")
                st.subheader("Example Rewrites")
                for idx, r in enumerate(feedback.get("rewrites", [])[:5], 1):
                    st.write(f"• {r}")
                st.subheader("ATS Advice")
                st.write(feedback.get("ats_advice", ""))
        except Exception as e:
            st.error(f"Error calling OpenAI: {e}")

    st.subheader("Rewrite a section")
    user_section = st.text_area("Paste the bullet/summary you want rewritten (or select below)", height=150)
    if st.button("Rewrite with missing keywords"):
        if not user_section.strip():
            st.warning("Paste a small section to be rewritten.")
        else:
            try:
                rewritten = rewrite_section(user_section, score_data.get("missing", []), role_hint="Target role from job description", model_choice=force_model)
                st.subheader("Rewritten section")
                st.write(rewritten)
            except Exception as e:
                st.error(f"Rewrite failed: {e}")

    if st.button("Export current resume text to DOCX"):
        doc = Document()
        for line in resume_text.splitlines():
            doc.add_paragraph(line)
        buf = BytesIO()
        doc.save(buf)
        buf.seek(0)
        st.download_button("Download DOCX", data=buf, file_name="resume_improved.docx")

else:
    st.info("Upload a resume and paste a job description to start.")
