"""PDF extraction tool."""

import os
import tempfile


def extract_pdf(path_or_url: str) -> dict:
    """Extract text from PDF file or URL.
    
    Returns: {"title": str, "content": str, "url": str, "source_type": "pdf"}
    Or: {"error": str}
    """
    try:
        import pymupdf
    except ImportError:
        return {"error": "pymupdf not installed. Run: pip install pymupdf"}
    
    try:
        pdf_path = path_or_url
        
        # Download if URL
        if path_or_url.startswith(("http://", "https://")):
            import urllib.request
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                urllib.request.urlretrieve(path_or_url, f.name)
                pdf_path = f.name
        
        if not os.path.exists(pdf_path):
            return {"error": f"File not found: {pdf_path}"}
        
        doc = pymupdf.open(pdf_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        
        content = "\n".join(text_parts)
        if not content.strip():
            return {"error": "No text found in PDF"}
        
        # Get title from metadata or filename
        title = doc.metadata.get("title") or os.path.basename(pdf_path).replace(".pdf", "")
        doc.close()
        
        return {
            "title": title,
            "content": content,
            "url": path_or_url,
            "source_type": "pdf",
        }
    except Exception as e:
        return {"error": f"PDF extraction failed: {e}"}
