"""Article extraction tool."""

import trafilatura


def extract_article(url: str) -> dict:
    """Extract text content from web article.
    
    Returns: {"title": str, "content": str, "url": str, "source_type": "article"}
    Or: {"error": str}
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return {"error": "Failed to download article"}
        
        content = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
        )
        if not content:
            return {"error": "Failed to extract content from article"}
        
        metadata = trafilatura.extract_metadata(downloaded)
        title = metadata.title if metadata and metadata.title else "Article"
        
        return {
            "title": title,
            "content": content,
            "url": url,
            "source_type": "article",
        }
    except Exception as e:
        return {"error": f"Article extraction failed: {e}"}
