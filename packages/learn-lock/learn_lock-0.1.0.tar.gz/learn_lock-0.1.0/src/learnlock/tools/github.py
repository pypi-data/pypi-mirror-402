"""GitHub repository extraction tool."""

import re


def extract_github(url: str) -> dict:
    """Extract README and key files from GitHub repo.
    
    Returns: {"title": str, "content": str, "url": str, "source_type": "github"}
    Or: {"error": str}
    """
    try:
        import requests
    except ImportError:
        return {"error": "requests not installed"}
    
    # Parse GitHub URL
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+)", url)
    if not match:
        return {"error": "Invalid GitHub URL"}
    
    owner, repo = match.groups()
    repo = repo.rstrip("/").split("/")[0]  # Remove trailing paths
    
    api_base = f"https://api.github.com/repos/{owner}/{repo}"
    
    try:
        # Get repo info
        resp = requests.get(api_base, timeout=10)
        if resp.status_code != 200:
            return {"error": f"GitHub API error: {resp.status_code}"}
        
        repo_info = resp.json()
        title = repo_info.get("name", repo)
        description = repo_info.get("description", "")
        
        # Get README
        readme_content = ""
        for readme_name in ["README.md", "README.rst", "README.txt", "README"]:
            readme_resp = requests.get(f"{api_base}/contents/{readme_name}", timeout=10)
            if readme_resp.status_code == 200:
                import base64
                readme_data = readme_resp.json()
                if readme_data.get("encoding") == "base64":
                    readme_content = base64.b64decode(readme_data["content"]).decode("utf-8", errors="ignore")
                    break
        
        if not readme_content:
            return {"error": "No README found in repository"}
        
        # Combine content
        content = f"# {title}\n\n{description}\n\n{readme_content}"
        
        return {
            "title": title,
            "content": content,
            "url": url,
            "source_type": "github",
        }
    except Exception as e:
        return {"error": f"GitHub extraction failed: {e}"}
