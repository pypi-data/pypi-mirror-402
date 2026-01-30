"""
Tests for zotero_mcp.cli module.

Tests cover:
- CLI argument parsing
- setup_environment function
- Command routing
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

from zotero_mcp.cli import setup_environment, main


class TestSetupEnvironment(unittest.TestCase):
    """Tests for setup_environment function."""

    @patch.dict(os.environ, {}, clear=True)
    @patch("zotero_mcp.cli.load_dotenv")
    def test_sets_default_library_id(self, mock_dotenv):
        """Sets default ZOTERO_LIBRARY_ID when not provided."""
        setup_environment()

        self.assertEqual(os.environ.get("ZOTERO_LIBRARY_ID"), "0")

    @patch.dict(os.environ, {"ZOTERO_LIBRARY_ID": "12345"}, clear=True)
    @patch("zotero_mcp.cli.load_dotenv")
    def test_respects_existing_library_id(self, mock_dotenv):
        """Respects existing ZOTERO_LIBRARY_ID setting."""
        setup_environment()

        self.assertEqual(os.environ.get("ZOTERO_LIBRARY_ID"), "12345")


class TestMainCLI(unittest.TestCase):
    """Tests for main CLI entry point."""

    @patch("sys.argv", ["zotero-mcp", "version"])
    @patch("zotero_mcp.cli.sys.exit")
    def test_version_command(self, mock_exit):
        """Version command prints version and exits."""
        with patch("builtins.print") as mock_print:
            main()

        mock_print.assert_called_once()
        call_arg = mock_print.call_args[0][0]
        self.assertIn("Zotero MCP Lite", call_arg)
        mock_exit.assert_called_once_with(0)

    @patch("sys.argv", ["zotero-mcp", "setup"])
    @patch("zotero_mcp.cli.sys.exit")
    @patch("zotero_mcp.setup_helper.main")
    def test_setup_command(self, mock_setup_main, mock_exit):
        """Setup command calls setup_helper.main."""
        mock_setup_main.return_value = 0
        main()

        mock_setup_main.assert_called_once()

    @patch("sys.argv", ["zotero-mcp", "serve"])
    @patch("zotero_mcp.cli.setup_environment")
    @patch("zotero_mcp.server.mcp")
    def test_serve_command_stdio(self, mock_mcp, mock_setup):
        """Serve command with default stdio transport."""
        main()

        mock_setup.assert_called_once()
        mock_mcp.run.assert_called_once_with(transport="stdio")

    @patch("sys.argv", ["zotero-mcp", "serve", "--transport", "streamable-http", "--port", "9000"])
    @patch("zotero_mcp.cli.setup_environment")
    @patch("zotero_mcp.server.mcp")
    def test_serve_command_http(self, mock_mcp, mock_setup):
        """Serve command with HTTP transport and custom port."""
        main()

        mock_mcp.run.assert_called_once_with(
            transport="streamable-http",
            host="localhost",
            port=9000,
        )

    @patch("sys.argv", ["zotero-mcp", "serve", "--transport", "sse", "--host", "0.0.0.0", "--port", "8080"])
    @patch("zotero_mcp.cli.setup_environment")
    @patch("zotero_mcp.server.mcp")
    def test_serve_command_sse(self, mock_mcp, mock_setup):
        """Serve command with SSE transport and custom host."""
        main()

        mock_mcp.run.assert_called_once_with(
            transport="sse",
            host="0.0.0.0",
            port=8080,
        )

    @patch("sys.argv", ["zotero-mcp"])
    @patch("zotero_mcp.cli.setup_environment")
    @patch("zotero_mcp.server.mcp")
    def test_default_to_serve_stdio(self, mock_mcp, mock_setup):
        """No command defaults to serve with stdio."""
        main()

        mock_setup.assert_called_once()
        mock_mcp.run.assert_called_once_with(transport="stdio")


class TestArgumentParsing(unittest.TestCase):
    """Tests for argument parsing edge cases."""

    @patch("sys.argv", ["zotero-mcp", "serve", "--transport", "invalid"])
    def test_invalid_transport_rejected(self):
        """Invalid transport value is rejected."""
        with self.assertRaises(SystemExit):
            main()

    @patch("sys.argv", ["zotero-mcp", "serve", "--port", "not_a_number"])
    def test_invalid_port_rejected(self):
        """Invalid port value is rejected."""
        with self.assertRaises(SystemExit):
            main()


if __name__ == "__main__":
    unittest.main()
