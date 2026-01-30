#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Zotero MCP Lite - Setup Helper
Auto-detect Zotero configuration and optionally configure MCP clients.
"""

import json
import os
import shutil
import sys
from pathlib import Path
from importlib import resources

from zotero_mcp.config import get_prompts_dir


def ensure_default_prompts() -> bool:
    """
    Copy default prompt files to user config directory if they don't exist.
    
    Returns:
        True if any files were created, False if all already existed.
    """
    prompts_dir = get_prompts_dir()
    prompts_dir.mkdir(parents=True, exist_ok=True)
    
    default_files = [
        "literature_review.md",
        "comparative_review.md",
        "knowledge_discovery.md",
        "bibliography_export.md",
    ]
    
    created = False
    
    # Get the path to the default_prompts package data
    try:
        pkg_prompts = resources.files("zotero_mcp.default_prompts")
        
        for filename in default_files:
            target_path = prompts_dir / filename
            if not target_path.exists():
                try:
                    content = (pkg_prompts / filename).read_text(encoding="utf-8")
                    target_path.write_text(content, encoding="utf-8")
                    created = True
                except Exception:
                    pass
    except Exception:
        pass
    
    return created


def find_zotero_data_dir() -> list[tuple[Path, bool]]:
    """
    Find all possible Zotero data directories.
    
    Returns:
        List of (path, has_database) tuples
    """
    home = Path.home()
    candidates = []
    
    if sys.platform == "win32":
        possible_paths = [
            home / "Zotero",
            Path(os.getenv("APPDATA", "")) / "Zotero" / "Zotero",
        ]
    elif sys.platform == "darwin":
        possible_paths = [
            home / "Zotero",
        ]
    else:  # Linux
        possible_paths = [
            home / "Zotero",
            home / ".zotero" / "zotero",
            home / "snap" / "zotero-snap" / "common" / "Zotero",
        ]
    
    for path in possible_paths:
        if path.exists():
            db_path = path / "zotero.sqlite"
            if not db_path.exists() and path.is_dir():
                for subdir in path.iterdir():
                    if subdir.is_dir():
                        sub_db = subdir / "zotero.sqlite"
                        if sub_db.exists():
                            candidates.append((subdir, True))
            else:
                candidates.append((path, db_path.exists()))
    
    return candidates


def check_local_api() -> tuple[bool, str, bool]:
    """
    Check if Zotero local API is accessible.
    
    Returns:
        (api_enabled, message, zotero_running) tuple
    """
    try:
        import httpx
        
        # First check if Zotero is running (connector endpoint is always enabled)
        try:
            ping = httpx.get("http://127.0.0.1:23119/connector/ping", timeout=3)
            zotero_running = "Zotero" in ping.text
        except Exception:
            zotero_running = False
        
        if not zotero_running:
            return False, "Zotero is not running", False
        
        # Now check the actual API endpoint
        response = httpx.get(
            "http://127.0.0.1:23119/api/users/0/items?limit=1",
            timeout=5
        )
        
        if response.status_code == 200:
            return True, "Local API is working", True
        elif response.status_code == 403:
            if "not enabled" in response.text.lower():
                return False, "Zotero running, but Local API not enabled", True
            return False, f"Access denied: {response.text}", True
        else:
            return False, f"Unexpected status: {response.status_code}", True
            
    except Exception as e:
        return False, f"Connection error: {e}", False


def get_claude_desktop_config_path() -> Path | None:
    """Get Claude Desktop config file path."""
    if sys.platform == "win32":
        config_path = Path(os.getenv("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
    elif sys.platform == "darwin":
        config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:  # Linux
        config_path = Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
    
    return config_path


def get_cursor_config_path() -> Path | None:
    """Get Cursor MCP config file path."""
    if sys.platform == "win32":
        return Path(os.getenv("APPDATA", "")) / "Cursor" / "User" / "globalStorage" / "cursor.mcp" / "mcp.json"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage" / "cursor.mcp" / "mcp.json"
    else:
        return Path.home() / ".config" / "Cursor" / "User" / "globalStorage" / "cursor.mcp" / "mcp.json"


def get_claude_code_config_path() -> Path | None:
    """Get Claude Code (CLI) MCP config file path."""
    # Claude Code uses the same config as Claude Desktop
    return Path.home() / ".claude" / "claude_desktop_config.json"


def find_zotero_mcp_command() -> str:
    """Find the zotero-mcp command path."""
    # Check if installed as a tool
    cmd = shutil.which("zotero-mcp")
    if cmd:
        return cmd
    
    # Fallback: use uvx for on-demand execution
    return "uvx"


def generate_mcp_config() -> dict:
    """Generate MCP server configuration for Zotero."""
    cmd = find_zotero_mcp_command()
    
    if cmd == "uvx":
        return {
            "command": "uvx",
            "args": ["--from", "git+https://github.com/xmruuu/zotero-mcp-lite.git", "zotero-mcp", "serve"]
        }
    else:
        return {
            "command": cmd,
            "args": ["serve"]
        }


def configure_mcp_client(client_name: str, config_path: Path, auto: bool = False) -> bool:
    """Configure an MCP client to use Zotero MCP."""
    if not config_path:
        print(f"  Could not determine {client_name} config path")
        return False
    
    # Create directory if needed
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing config or create new
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError:
            config = {}
    else:
        config = {}
    
    # Ensure mcpServers exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Check if already configured
    if "zotero" in config["mcpServers"]:
        print(f"  [OK] Zotero already configured in {client_name}")
        return True
    
    # Add Zotero config
    config["mcpServers"]["zotero"] = generate_mcp_config()
    
    if not auto:
        print(f"\n  Config file: {config_path}")
        print(f"  Will add Zotero MCP server configuration")
        response = input("  Proceed? [Y/n]: ").strip().lower()
        if response and response != "y":
            print("  Skipped")
            return False
    
    # Backup existing config
    if config_path.exists():
        backup_path = config_path.with_suffix(".json.backup")
        shutil.copy(config_path, backup_path)
        print(f"  Backup saved: {backup_path}")
    
    # Write new config
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    print(f"  [OK] {client_name} configured!")
    return True


def configure_claude_desktop(auto: bool = False) -> bool:
    """Configure Claude Desktop to use Zotero MCP."""
    return configure_mcp_client("Claude Desktop", get_claude_desktop_config_path(), auto)


def configure_cursor(auto: bool = False) -> bool:
    """Configure Cursor to use Zotero MCP."""
    return configure_mcp_client("Cursor", get_cursor_config_path(), auto)


def print_manual_config():
    """Print manual configuration instructions."""
    config = generate_mcp_config()
    config_json = json.dumps({"mcpServers": {"zotero": config}}, indent=2)
    
    print("\n  Add this to your MCP client config:\n")
    print("  " + config_json.replace("\n", "\n  "))


def main():
    """Main setup wizard."""
    print()
    print("=" * 60)
    print("  Zotero MCP Lite - Setup")
    print("=" * 60)
    print()
    
    # Step 1: Check Zotero data directory
    print("[1/4] Detecting Zotero installation...")
    print("-" * 40)
    
    found_dirs = find_zotero_data_dir()
    best_dir = None
    
    if not found_dirs:
        print("  [!!] No Zotero data directory found")
        print("  Make sure Zotero has been run at least once")
    else:
        for path, has_db in found_dirs:
            if has_db:
                best_dir = path
                print(f"  [OK] Found: {path}")
                break
        if not best_dir:
            print("  [!!] Zotero directory found but no database")
    
    print()
    
    # Step 2: Check local API
    print("[2/4] Checking Zotero local API...")
    print("-" * 40)
    
    api_ok, api_msg, zotero_running = check_local_api()
    
    if api_ok:
        print(f"  [OK] {api_msg}")
    else:
        print(f"  [!!] {api_msg}")
        print()
        if not zotero_running:
            print("  Please start Zotero and run this command again.")
        else:
            print("  Zotero is running but the Local API is not enabled.")
            print()
            print("  To enable Local API in Zotero 7:")
            print("  1. Open Zotero -> Edit -> Settings")
            print("  2. Go to Advanced -> General")
            print("  3. Check 'Allow other applications on this computer")
            print("     to communicate with Zotero'")
    
    print()
    
    # Step 3: Configure MCP client
    print("[3/4] MCP Client Configuration...")
    print("-" * 40)
    
    claude_desktop_path = get_claude_desktop_config_path()
    claude_code_path = get_claude_code_config_path()
    cursor_path = get_cursor_config_path()
    
    clients_found = []
    if claude_desktop_path and claude_desktop_path.parent.exists():
        clients_found.append(("Claude Desktop", claude_desktop_path))
    if claude_code_path and claude_code_path.parent.exists():
        clients_found.append(("Claude Code (CLI)", claude_code_path))
    if cursor_path and cursor_path.parent.exists():
        clients_found.append(("Cursor", cursor_path))
    
    if clients_found:
        print(f"  Found MCP clients: {', '.join(c[0] for c in clients_found)}")
        
        for client_name, config_path in clients_found:
            print(f"\n  Configure {client_name}?")
            configure_mcp_client(client_name, config_path, auto=False)
    else:
        print("  No MCP clients detected (Claude Desktop, Cursor)")
        print_manual_config()
    
    # Step 4: Setup default prompts
    print()
    print("[4/4] Setting up prompt templates...")
    print("-" * 40)
    
    prompts_dir = get_prompts_dir()
    if ensure_default_prompts():
        print(f"  [OK] Created default prompts in: {prompts_dir}")
    else:
        print(f"  [OK] Prompts directory ready: {prompts_dir}")
    print("  You can customize these files to change how reviews are generated.")
    
    # Summary
    print()
    print("=" * 60)
    print("  Setup Complete!")
    print("=" * 60)
    
    if best_dir and api_ok:
        print()
        print("  Ready to use! Start the server with:")
        print()
        print("    zotero-mcp serve")
        print()
        print(f"  Customize prompts at: {prompts_dir}")
        print()
        return 0
    else:
        print()
        print("  [!!] Please fix the issues above before using")
        print()
        if not api_ok:
            print("  Most common fix: Enable local API in Zotero settings")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
