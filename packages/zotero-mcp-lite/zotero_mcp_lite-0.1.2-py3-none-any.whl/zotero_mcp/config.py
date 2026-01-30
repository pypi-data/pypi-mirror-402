"""
Configuration management for Zotero MCP.

Handles loading of user-customizable prompt files.

Loading order:
1. User directory: ~/.zotero-mcp/prompts/ (takes priority)
2. Package defaults: zotero_mcp/default_prompts/
"""

from pathlib import Path
from importlib import resources


def get_user_config_dir() -> Path:
    """Get the user config directory (~/.zotero-mcp/)."""
    return Path.home() / ".zotero-mcp"


def get_prompts_dir() -> Path:
    """Get the prompts directory (~/.zotero-mcp/prompts/)."""
    return get_user_config_dir() / "prompts"


def _load_default_prompt(name: str) -> str | None:
    """Load a prompt from package default_prompts directory."""
    try:
        return resources.files("zotero_mcp.default_prompts").joinpath(f"{name}.md").read_text(encoding="utf-8")
    except (FileNotFoundError, TypeError):
        return None


def load_prompt(name: str) -> str | None:
    """
    Load a prompt file with fallback to package defaults.
    
    Loading order:
    1. ~/.zotero-mcp/prompts/{name}.md (user customization)
    2. zotero_mcp/default_prompts/{name}.md (package default)
    
    Args:
        name: Prompt name (e.g., "literature_review")
    
    Returns:
        Prompt content string, or None if not found anywhere.
    """
    # 1. Try user directory first
    prompt_path = get_prompts_dir() / f"{name}.md"
    if prompt_path.exists():
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except IOError:
            pass
    
    # 2. Fallback to package defaults
    return _load_default_prompt(name)


def ensure_prompts_dir() -> Path:
    """
    Ensure the prompts directory exists.
    
    Returns:
        Path to the prompts directory.
    """
    prompts_dir = get_prompts_dir()
    prompts_dir.mkdir(parents=True, exist_ok=True)
    return prompts_dir
