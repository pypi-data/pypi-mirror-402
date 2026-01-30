"""
Command-line interface for Zotero MCP Lite server.
"""

import argparse
import os
import sys

from dotenv import load_dotenv


def setup_environment():
    """Load environment variables from .env file."""
    load_dotenv()
    
    # Set defaults for local mode
    os.environ.setdefault("ZOTERO_LIBRARY_ID", "0")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Zotero MCP Lite - A lightweight MCP server for Zotero"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Run the MCP server")
    serve_parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
        help="Transport protocol (default: stdio)"
    )
    serve_parser.add_argument(
        "--host",
        default="localhost",
        help="Host for HTTP transports (default: localhost)"
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP transports (default: 8000)"
    )
    
    # Version command
    subparsers.add_parser("version", help="Print version information")
    
    # Setup command
    subparsers.add_parser("setup", help="Detect Zotero configuration and show setup guide")
    
    args = parser.parse_args()
    
    # Default to serve with stdio if no command provided
    if not args.command:
        args.command = "serve"
        args.transport = "stdio"
        args.host = "localhost"
        args.port = 8000
    
    if args.command == "version":
        from zotero_mcp._version import __version__
        print(f"Zotero MCP Lite v{__version__}")
        sys.exit(0)
    
    elif args.command == "setup":
        from zotero_mcp.setup_helper import main as setup_main
        sys.exit(setup_main())
    
    elif args.command == "serve":
        setup_environment()
        
        from zotero_mcp.server import mcp
        
        if args.transport == "stdio":
            mcp.run(transport="stdio")
        elif args.transport == "streamable-http":
            mcp.run(transport="streamable-http", host=args.host, port=args.port)
        elif args.transport == "sse":
            mcp.run(transport="sse", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
