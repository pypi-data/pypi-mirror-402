"""Sync module for downloading and caching templates from GitHub."""

from pathlib import Path
from typing import Optional

import httpx

# GitHub raw URLs for template files
GITHUB_REPO = "Alaa-Taieb/agentic-std"
GITHUB_BRANCH = "main"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"

TEMPLATE_FILES = [
    "blueprint.md",
    "rules.md",
    "vibe-guide.md",
    "journal.md",
]


def get_cache_dir() -> Path:
    """Get the cache directory for templates (~/.acs/templates/)."""
    return Path.home() / ".acs" / "templates"


def get_bundled_templates_dir() -> Path:
    """Get the bundled templates directory (fallback)."""
    return Path(__file__).parent / "templates"


def get_templates_dir() -> Path:
    """
    Get the templates directory to use.
    
    Returns cached templates if available, otherwise bundled templates.
    """
    cache_dir = get_cache_dir()
    
    # Check if cache exists and has all template files
    if cache_dir.exists():
        cached_files = [f.name for f in cache_dir.glob("*.md")]
        if all(template in cached_files for template in TEMPLATE_FILES):
            return cache_dir
    
    # Fall back to bundled templates
    return get_bundled_templates_dir()


def download_templates(timeout: float = 30.0) -> tuple[bool, Optional[str]]:
    """
    Download templates from GitHub and save to cache.
    
    Returns:
        tuple: (success: bool, error_message: Optional[str])
    """
    cache_dir = get_cache_dir()
    
    try:
        # Create cache directory
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Download each template file
        with httpx.Client(timeout=timeout) as client:
            for template_name in TEMPLATE_FILES:
                url = f"{GITHUB_RAW_BASE}/src/acs_cli/templates/{template_name}"
                response = client.get(url)
                response.raise_for_status()
                
                # Save to cache
                template_path = cache_dir / template_name
                template_path.write_text(response.text, encoding="utf-8")
        
        return True, None
        
    except httpx.HTTPStatusError as e:
        return False, f"HTTP error: {e.response.status_code}"
    except httpx.RequestError as e:
        return False, f"Network error: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def get_cache_info() -> dict:
    """Get information about the cached templates."""
    cache_dir = get_cache_dir()
    
    if not cache_dir.exists():
        return {"exists": False, "path": str(cache_dir), "files": []}
    
    files = list(cache_dir.glob("*.md"))
    return {
        "exists": True,
        "path": str(cache_dir),
        "files": [f.name for f in files],
        "file_count": len(files),
    }
