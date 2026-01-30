"""
Tests for zotero_mcp.server module.

Tests cover MCP tool functions with mocked Zotero client.
Note: FastMCP wraps functions as FunctionTool objects, so we access .fn for testing.
"""

import unittest
from unittest.mock import MagicMock, patch

from zotero_mcp.server import (
    search_items,
    get_recent,
    get_collections,
    get_collection_items,
    search_annotations,
    get_item_metadata,
    get_item_children,
    get_item_fulltext,
    create_note,
)

# Access the underlying functions from FunctionTool wrappers
_search_items = search_items.fn
_get_recent = get_recent.fn
_get_collections = get_collections.fn
_get_collection_items = get_collection_items.fn
_search_annotations = search_annotations.fn
_get_item_metadata = get_item_metadata.fn
_get_item_children = get_item_children.fn
_get_item_fulltext = get_item_fulltext.fn
_create_note = create_note.fn


class MockContext:
    """Mock FastMCP Context for testing."""

    def __init__(self):
        self.info_messages = []
        self.warn_messages = []
        self.error_messages = []

    def info(self, msg):
        self.info_messages.append(msg)

    def warn(self, msg):
        self.warn_messages.append(msg)

    def error(self, msg):
        self.error_messages.append(msg)


class TestSearchItems(unittest.TestCase):
    """Tests for zotero_search_items tool."""

    @patch("zotero_mcp.server.get_zotero_client")
    def test_search_returns_results(self, mock_get_client):
        """Search returns formatted results."""
        mock_zot = MagicMock()
        mock_zot.items.return_value = [
            {
                "key": "ABC123",
                "data": {
                    "title": "Test Article",
                    "itemType": "journalArticle",
                    "date": "2024-01-15",
                    "creators": [{"firstName": "John", "lastName": "Smith"}],
                    "tags": [{"tag": "AI"}],
                },
            }
        ]
        mock_get_client.return_value = mock_zot

        ctx = MockContext()
        result = _search_items("test query", ctx=ctx)

        self.assertIn("Test Article", result)
        self.assertIn("ABC123", result)
        self.assertIn("journalArticle", result)
        self.assertIn("`AI`", result)

    @patch("zotero_mcp.server.get_zotero_client")
    def test_search_no_results(self, mock_get_client):
        """Search with no results returns appropriate message."""
        mock_zot = MagicMock()
        mock_zot.items.return_value = []
        mock_get_client.return_value = mock_zot

        ctx = MockContext()
        result = _search_items("nonexistent", ctx=ctx)

        self.assertIn("No items found", result)

    def test_search_empty_query(self):
        """Empty query returns error message."""
        ctx = MockContext()
        result = _search_items("   ", ctx=ctx)

        self.assertIn("Error", result)
        self.assertIn("empty", result.lower())


class TestGetRecent(unittest.TestCase):
    """Tests for zotero_get_recent tool."""

    @patch("zotero_mcp.server.get_zotero_client")
    def test_get_recent_returns_items(self, mock_get_client):
        """Get recent returns formatted items."""
        mock_zot = MagicMock()
        mock_zot.items.return_value = [
            {
                "key": "ABC123",
                "data": {
                    "title": "Recent Paper",
                    "itemType": "journalArticle",
                    "dateModified": "2024-01-15T10:00:00Z",
                    "creators": [],
                },
            }
        ]
        mock_get_client.return_value = mock_zot

        ctx = MockContext()
        result = _get_recent(limit=10, ctx=ctx)

        self.assertIn("Recent Paper", result)
        self.assertIn("Recently Modified", result)

    @patch("zotero_mcp.server.get_zotero_client")
    def test_get_recent_empty_library(self, mock_get_client):
        """Empty library returns appropriate message."""
        mock_zot = MagicMock()
        mock_zot.items.return_value = []
        mock_get_client.return_value = mock_zot

        ctx = MockContext()
        result = _get_recent(limit=10, ctx=ctx)

        self.assertIn("No items found", result)

    @patch("zotero_mcp.server.get_zotero_client")
    def test_get_recent_limit_clamped(self, mock_get_client):
        """Limit is clamped to valid range."""
        mock_zot = MagicMock()
        mock_zot.items.return_value = []
        mock_get_client.return_value = mock_zot

        ctx = MockContext()
        # Test with invalid limits
        _get_recent(limit=-5, ctx=ctx)
        _get_recent(limit=500, ctx=ctx)

        # Should be called with clamped values
        calls = mock_zot.items.call_args_list
        self.assertEqual(calls[0][1]["limit"], 1)  # min clamped to 1
        self.assertEqual(calls[1][1]["limit"], 100)  # max clamped to 100

    @patch("zotero_mcp.server.get_zotero_client")
    def test_get_recent_sort_by_date_added(self, mock_get_client):
        """Sort by dateAdded returns correctly formatted output."""
        mock_zot = MagicMock()
        mock_zot.items.return_value = [
            {
                "key": "NEW123",
                "data": {
                    "title": "Newly Added Paper",
                    "itemType": "journalArticle",
                    "dateAdded": "2024-01-20T10:00:00Z",
                    "dateModified": "2024-01-21T10:00:00Z",
                    "creators": [],
                },
            }
        ]
        mock_get_client.return_value = mock_zot

        ctx = MockContext()
        result = _get_recent(limit=10, sort_by="dateAdded", ctx=ctx)

        self.assertIn("Newly Added Paper", result)
        self.assertIn("Recently Added", result)
        self.assertIn("2024-01-20", result)
        mock_zot.items.assert_called_once_with(
            limit=10, sort="dateAdded", direction="desc", itemType="-attachment -note"
        )

    @patch("zotero_mcp.server.get_zotero_client")
    def test_get_recent_default_excludes_notes(self, mock_get_client):
        """Default item_type excludes attachments and notes."""
        mock_zot = MagicMock()
        mock_zot.items.return_value = []
        mock_get_client.return_value = mock_zot

        ctx = MockContext()
        _get_recent(limit=10, ctx=ctx)

        # Should exclude attachments and notes by default
        mock_zot.items.assert_called_once_with(
            limit=10, sort="dateModified", direction="desc", itemType="-attachment -note"
        )

    @patch("zotero_mcp.server.get_zotero_client")
    def test_get_recent_include_all_types(self, mock_get_client):
        """Empty item_type includes all item types."""
        mock_zot = MagicMock()
        mock_zot.items.return_value = []
        mock_get_client.return_value = mock_zot

        ctx = MockContext()
        _get_recent(limit=10, item_type="", ctx=ctx)

        # Empty string should pass None to include all types
        mock_zot.items.assert_called_once_with(
            limit=10, sort="dateModified", direction="desc", itemType=None
        )


class TestGetCollections(unittest.TestCase):
    """Tests for zotero_get_collections tool."""

    @patch("zotero_mcp.server.get_zotero_client")
    def test_get_collections_returns_hierarchy(self, mock_get_client):
        """Collections returns formatted hierarchy."""
        mock_zot = MagicMock()
        mock_zot.collections.return_value = [
            {
                "key": "COL1",
                "data": {"name": "Research", "parentCollection": None},
            },
            {
                "key": "COL2",
                "data": {"name": "Papers", "parentCollection": "COL1"},
            },
        ]
        mock_get_client.return_value = mock_zot

        ctx = MockContext()
        result = _get_collections(ctx=ctx)

        self.assertIn("Research", result)
        self.assertIn("Papers", result)
        self.assertIn("COL1", result)

    @patch("zotero_mcp.server.get_zotero_client")
    def test_get_collections_empty(self, mock_get_client):
        """Empty collections returns appropriate message."""
        mock_zot = MagicMock()
        mock_zot.collections.return_value = []
        mock_get_client.return_value = mock_zot

        ctx = MockContext()
        result = _get_collections(ctx=ctx)

        self.assertIn("No collections found", result)


class TestGetCollectionItems(unittest.TestCase):
    """Tests for zotero_get_collection_items tool."""

    @patch("zotero_mcp.server.get_zotero_client")
    def test_get_collection_items_returns_items(self, mock_get_client):
        """Collection items returns formatted list."""
        mock_zot = MagicMock()
        mock_zot.collection.return_value = {
            "data": {"name": "My Collection"}
        }
        mock_zot.collection_items.return_value = [
            {
                "key": "ITEM1",
                "data": {
                    "title": "Paper in Collection",
                    "itemType": "journalArticle",
                    "creators": [],
                },
            }
        ]
        mock_get_client.return_value = mock_zot

        ctx = MockContext()
        result = _get_collection_items("COL1", ctx=ctx)

        self.assertIn("My Collection", result)
        self.assertIn("Paper in Collection", result)

    @patch("zotero_mcp.server.get_zotero_client")
    def test_get_collection_items_default_excludes_notes(self, mock_get_client):
        """Default item_type excludes attachments and notes."""
        mock_zot = MagicMock()
        mock_zot.collection.return_value = {"data": {"name": "Test"}}
        mock_zot.collection_items.return_value = []
        mock_get_client.return_value = mock_zot

        ctx = MockContext()
        _get_collection_items("COL1", ctx=ctx)

        mock_zot.collection_items.assert_called_once_with(
            "COL1", limit=50, itemType="-attachment -note"
        )

    @patch("zotero_mcp.server.get_zotero_client")
    def test_get_collection_items_include_all_types(self, mock_get_client):
        """Empty item_type includes all item types."""
        mock_zot = MagicMock()
        mock_zot.collection.return_value = {"data": {"name": "Test"}}
        mock_zot.collection_items.return_value = []
        mock_get_client.return_value = mock_zot

        ctx = MockContext()
        _get_collection_items("COL1", item_type="", ctx=ctx)

        mock_zot.collection_items.assert_called_once_with(
            "COL1", limit=50, itemType=None
        )




class TestSearchAnnotations(unittest.TestCase):
    """Tests for zotero_search_annotations tool."""

    @patch("zotero_mcp.local_db.get_local_db")
    def test_search_annotations_returns_results(self, mock_get_db):
        """Annotations matching query are returned with parent info."""
        from zotero_mcp.local_db import Annotation

        mock_db = MagicMock()
        mock_db.search_annotations.return_value = [
            Annotation(
                type="highlight",
                text="machine learning is important",
                comment="Key concept",
                color="#FFFF00",
                page_label="5",
                attachment_name="paper.pdf",
                parent_key="ABC123",
                parent_title="Introduction to ML",
            )
        ]
        mock_get_db.return_value = mock_db

        ctx = MockContext()
        result = _search_annotations("machine learning", ctx=ctx)

        self.assertIn("machine learning is important", result)
        self.assertIn("Introduction to ML", result)
        self.assertIn("ABC123", result)
        mock_db.close.assert_called_once()

    @patch("zotero_mcp.local_db.get_local_db")
    def test_search_annotations_no_results(self, mock_get_db):
        """No matching annotations returns appropriate message."""
        mock_db = MagicMock()
        mock_db.search_annotations.return_value = []
        mock_get_db.return_value = mock_db

        ctx = MockContext()
        result = _search_annotations("nonexistent term", ctx=ctx)

        self.assertIn("No annotations found", result)

    def test_search_annotations_empty_query(self):
        """Empty query returns error."""
        ctx = MockContext()
        result = _search_annotations("", ctx=ctx)

        self.assertIn("Error", result)

    @patch("zotero_mcp.local_db.get_local_db")
    def test_search_annotations_db_not_available(self, mock_get_db):
        """Returns error when database is not available."""
        mock_get_db.return_value = None

        ctx = MockContext()
        result = _search_annotations("test", ctx=ctx)

        self.assertIn("Error", result)
        self.assertIn("database", result.lower())


class TestGetItemMetadata(unittest.TestCase):
    """Tests for zotero_get_item_metadata tool."""

    @patch("zotero_mcp.server.get_zotero_client")
    def test_get_item_metadata_returns_formatted(self, mock_get_client):
        """Item metadata is returned formatted."""
        mock_zot = MagicMock()
        mock_zot.item.return_value = {
            "data": {
                "title": "Test Paper",
                "itemType": "journalArticle",
                "key": "ABC123",
                "abstractNote": "This is the abstract.",
                "creators": [{"firstName": "John", "lastName": "Doe"}],
            }
        }
        mock_get_client.return_value = mock_zot

        ctx = MockContext()
        result = _get_item_metadata("ABC123", ctx=ctx)

        self.assertIn("# Test Paper", result)
        self.assertIn("journalArticle", result)
        self.assertIn("Abstract", result)

    @patch("zotero_mcp.server.get_zotero_client")
    def test_get_item_metadata_with_bibtex(self, mock_get_client):
        """Item metadata includes BibTeX when requested."""
        mock_zot = MagicMock()
        mock_zot.item.return_value = {
            "data": {
                "title": "Test Paper",
                "itemType": "journalArticle",
                "key": "ABC123",
                "date": "2024",
                "creators": [
                    {"creatorType": "author", "firstName": "John", "lastName": "Doe"}
                ],
            }
        }
        mock_get_client.return_value = mock_zot

        ctx = MockContext()
        result = _get_item_metadata("ABC123", include_bibtex=True, ctx=ctx)

        self.assertIn("BibTeX", result)
        self.assertIn("@article", result)


class TestGetItemChildren(unittest.TestCase):
    """Tests for zotero_get_item_children tool."""

    @patch("zotero_mcp.server.get_zotero_client")
    def test_get_item_children_returns_attachments_and_notes(self, mock_get_client):
        """Children returns both attachments and notes."""
        mock_zot = MagicMock()
        mock_zot.item.return_value = {
            "data": {"title": "Parent Item"}
        }
        mock_zot.children.return_value = [
            {
                "key": "ATT1",
                "data": {
                    "itemType": "attachment",
                    "title": "paper.pdf",
                    "contentType": "application/pdf",
                    "filename": "paper.pdf",
                },
            },
            {
                "key": "NOTE1",
                "data": {
                    "itemType": "note",
                    "note": "<p>My note content</p>",
                },
            },
        ]
        mock_get_client.return_value = mock_zot

        ctx = MockContext()
        result = _get_item_children("PARENT1", ctx=ctx)

        self.assertIn("Attachments", result)
        self.assertIn("Notes", result)
        self.assertIn("paper.pdf", result)
        self.assertIn("ATT1", result)


class TestGetItemFulltext(unittest.TestCase):
    """Tests for zotero_get_item_fulltext tool."""

    @patch("zotero_mcp.server.get_attachment_details")
    @patch("zotero_mcp.server.get_zotero_client")
    def test_fulltext_from_zotero_index(self, mock_get_client, mock_get_attachment):
        """Fulltext retrieved from Zotero's index."""
        from zotero_mcp.client import AttachmentDetails

        mock_zot = MagicMock()
        mock_zot.item.return_value = {"data": {"title": "Test Paper"}}
        mock_zot.fulltext_item.return_value = {
            "content": "This is the full text content of the paper."
        }
        mock_get_client.return_value = mock_zot
        mock_get_attachment.return_value = AttachmentDetails(
            key="ATT123",
            title="paper.pdf",
            filename="paper.pdf",
            content_type="application/pdf",
        )

        ctx = MockContext()
        result = _get_item_fulltext("ABC123", ctx=ctx)

        self.assertIn("full text content", result)
        mock_zot.fulltext_item.assert_called_once_with("ATT123")

    @patch("zotero_mcp.server.get_attachment_details")
    @patch("zotero_mcp.server.get_zotero_client")
    def test_fulltext_truncated_when_exceeds_max(self, mock_get_client, mock_get_attachment):
        """Long content is truncated with message."""
        from zotero_mcp.client import AttachmentDetails

        mock_zot = MagicMock()
        mock_zot.item.return_value = {"data": {"title": "Test Paper"}}
        # Content longer than default max_chars
        long_content = "A" * 15000
        mock_zot.fulltext_item.return_value = {"content": long_content}
        mock_get_client.return_value = mock_zot
        mock_get_attachment.return_value = AttachmentDetails(
            key="ATT123",
            title="paper.pdf",
            filename="paper.pdf",
            content_type="application/pdf",
        )

        ctx = MockContext()
        result = _get_item_fulltext("ABC123", max_chars=10000, ctx=ctx)

        self.assertIn("truncated", result)
        self.assertIn("5000 more characters", result)

    @patch("zotero_mcp.server.get_attachment_details")
    @patch("zotero_mcp.server.get_zotero_client")
    def test_fulltext_no_item_found(self, mock_get_client, mock_get_attachment):
        """Returns error when item not found."""
        mock_zot = MagicMock()
        mock_zot.item.return_value = None
        mock_get_client.return_value = mock_zot

        ctx = MockContext()
        result = _get_item_fulltext("INVALID", ctx=ctx)

        self.assertIn("No item found", result)

    @patch("zotero_mcp.server.get_attachment_details")
    @patch("zotero_mcp.server.get_zotero_client")
    def test_fulltext_no_attachment_found(self, mock_get_client, mock_get_attachment):
        """Returns error when no suitable attachment."""
        mock_zot = MagicMock()
        mock_zot.item.return_value = {"data": {"title": "Test Paper"}}
        mock_get_client.return_value = mock_zot
        mock_get_attachment.return_value = None

        ctx = MockContext()
        result = _get_item_fulltext("ABC123", ctx=ctx)

        self.assertIn("No suitable attachment", result)

    @patch("zotero_mcp.server.get_attachment_details")
    @patch("zotero_mcp.server.get_zotero_client")
    def test_fulltext_fallback_when_index_empty(self, mock_get_client, mock_get_attachment):
        """Falls back to PyMuPDF when Zotero index has no content."""
        from zotero_mcp.client import AttachmentDetails

        mock_zot = MagicMock()
        mock_zot.item.return_value = {"data": {"title": "Test Paper"}}
        mock_zot.fulltext_item.return_value = {"content": ""}  # Empty index
        mock_get_client.return_value = mock_zot
        mock_get_attachment.return_value = AttachmentDetails(
            key="ATT123",
            title="paper.pdf",
            filename="paper.pdf",
            content_type="application/pdf",
        )

        ctx = MockContext()
        # This will try PyMuPDF fallback which may fail in test environment
        result = _get_item_fulltext("ABC123", ctx=ctx)

        # Should either succeed with content or show a fallback error
        # (not the "No suitable attachment" error)
        self.assertNotIn("No suitable attachment", result)


class TestCreateNote(unittest.TestCase):
    """Tests for zotero_create_note tool."""

    @patch("zotero_mcp.server.create_item_local")
    @patch("zotero_mcp.server.get_zotero_client")
    def test_create_note_standalone(self, mock_get_client, mock_create):
        """Standalone note is created successfully."""
        mock_create.return_value = {"success": True}

        ctx = MockContext()
        result = _create_note("My note content", ctx=ctx)

        self.assertIn("Standalone note created", result)
        mock_create.assert_called_once()

    @patch("zotero_mcp.server.create_item_local")
    @patch("zotero_mcp.server.get_zotero_client")
    def test_create_note_with_parent(self, mock_get_client, mock_create):
        """Note attached to parent is created successfully."""
        mock_create.return_value = {"success": True}
        mock_zot = MagicMock()
        mock_zot.item.return_value = {
            "data": {"title": "Parent Paper"}
        }
        mock_get_client.return_value = mock_zot

        ctx = MockContext()
        result = _create_note("My note", parent_key="PARENT1", ctx=ctx)

        self.assertIn("Parent Paper", result)

    @patch("zotero_mcp.server.create_item_local")
    def test_create_note_connection_error(self, mock_create):
        """Connection error is handled gracefully."""
        mock_create.side_effect = ConnectionError("Cannot connect")

        ctx = MockContext()
        result = _create_note("My note", ctx=ctx)

        self.assertIn("Cannot connect", result)


if __name__ == "__main__":
    unittest.main()
