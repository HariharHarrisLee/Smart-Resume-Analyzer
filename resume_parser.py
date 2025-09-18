# resume_parser.py
import io
import os
import tempfile

def extract_text(uploaded_file) -> str:
    """
    Accepts streamlit uploaded file or path string.
    Returns plain text.
    """
    if hasattr(uploaded_file, "read"):
        data = uploaded_file.read()
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        filename = getattr(uploaded_file, "name", "uploaded")
        ext = filename.split(".")[-1].lower()
        return _extract_bytes(data, ext)
    elif isinstance(uploaded_file, str):
        ext = uploaded_file.split(".")[-1].lower()
        with open(uploaded_file, "rb") as f:
            data = f.read()
        return _extract_bytes(data, ext)
    else:
        return ""

def _extract_bytes(data: bytes, ext: str) -> str:
    text = ""
    if ext == "pdf":
        try:
            import pdfplumber
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(data)
                tmp.flush()
                tmp_path = tmp.name
            with pdfplumber.open(tmp_path) as pdf:
                for p in pdf.pages:
                    page_text = p.extract_text()
                    if page_text:
                        text += page_text + "\n"
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        except Exception:
            try:
                text = data.decode("utf-8", errors="ignore")
            except:
                text = ""
    elif ext in ("docx", "doc"):
        try:
            from docx import Document
            doc = Document(io.BytesIO(data))
            paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
            text = "\n".join(paragraphs)
        except Exception:
            text = ""
    else:
        try:
            text = data.decode("utf-8", errors="ignore")
        except Exception:
            text = ""
    return text
