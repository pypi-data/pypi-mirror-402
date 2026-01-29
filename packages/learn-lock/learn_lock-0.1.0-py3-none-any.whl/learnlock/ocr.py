"""OCR utility for extracting text from images."""

import os
from pathlib import Path


def extract_text_from_image(image_path: str) -> dict:
    """Extract text from image using OCR.
    
    Returns: {"text": str, "confidence": float}
    Or: {"error": str}
    """
    path = Path(image_path)
    
    if not path.exists():
        return {"error": f"File not found: {image_path}"}
    
    if path.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"):
        return {"error": f"Unsupported image format: {path.suffix}"}
    
    # Try EasyOCR first (better accuracy, works offline)
    result = _try_easyocr(str(path))
    if "error" not in result:
        return result
    
    # Fallback to Tesseract if available
    result = _try_tesseract(str(path))
    if "error" not in result:
        return result
    
    return {"error": "No OCR engine available. Install: pip install easyocr"}


def check_relevance(text: str, concept_name: str, source_quote: str) -> dict:
    """Check if extracted text is relevant to the concept.
    
    Returns: {"is_relevant": bool, "reason": str}
    """
    if not text or len(text.strip()) < 10:
        return {"is_relevant": False, "reason": "Text too short"}
    
    # Use LLM to check relevance
    try:
        from . import config
        import os
        
        prompt = f"""Is this text relevant to explaining the concept "{concept_name}"?

Concept context: "{source_quote[:200]}"

Text to check: "{text[:500]}"

Reply with ONLY "yes" or "no" followed by a brief reason.
Example: "yes - discusses the core mechanism"
Example: "no - unrelated content about cooking"
"""
        
        # Try Groq for quick check
        if os.environ.get("GROQ_API_KEY"):
            import litellm
            litellm.suppress_debug_info = True
            response = litellm.completion(
                model=f"groq/{config.GROQ_MODEL}",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.1,
            )
            answer = response.choices[0].message.content.lower().strip()
            is_relevant = answer.startswith("yes")
            return {"is_relevant": is_relevant, "reason": answer}
        
        # No API key - do basic keyword check
        concept_words = set(concept_name.lower().split())
        text_words = set(text.lower().split())
        overlap = concept_words & text_words
        is_relevant = len(overlap) > 0 or len(text) > 50
        return {"is_relevant": is_relevant, "reason": "keyword match" if is_relevant else "no keywords found"}
        
    except Exception:
        # On error, assume relevant to not block user
        return {"is_relevant": True, "reason": "check skipped"}


def _try_easyocr(image_path: str) -> dict:
    """Try OCR with EasyOCR."""
    try:
        import easyocr
    except ImportError:
        return {"error": "easyocr not installed"}
    
    try:
        # Initialize reader (cached after first use)
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        results = reader.readtext(image_path)
        
        if not results:
            return {"text": "", "confidence": 0.0}
        
        # Combine all detected text
        texts = []
        confidences = []
        for (bbox, text, conf) in results:
            texts.append(text)
            confidences.append(conf)
        
        combined_text = " ".join(texts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {"text": combined_text, "confidence": avg_confidence}
    except Exception as e:
        return {"error": f"EasyOCR failed: {e}"}


def _try_tesseract(image_path: str) -> dict:
    """Try OCR with Tesseract (via pytesseract)."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return {"error": "pytesseract not installed"}
    
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        
        # Tesseract doesn't give confidence easily, estimate from text quality
        confidence = 0.8 if text.strip() else 0.0
        
        return {"text": text.strip(), "confidence": confidence}
    except Exception as e:
        return {"error": f"Tesseract failed: {e}"}


def is_image_file(path: str) -> bool:
    """Check if path is a supported image file."""
    if not os.path.exists(path):
        return False
    return Path(path).suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")
