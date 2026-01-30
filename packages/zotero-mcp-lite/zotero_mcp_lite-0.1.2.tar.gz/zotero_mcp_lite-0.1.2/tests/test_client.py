"""
Tests for zotero_mcp.client module.

Tests cover:
- AttachmentDetails: Dataclass creation
- format_item_metadata: Markdown formatting
- generate_bibtex: BibTeX generation
- get_zotero_client: Client initialization (mocked)
"""

import unittest
from unittest.mock import patch

from zotero_mcp.client import (
    AttachmentDetails,
    format_item_metadata,
    generate_bibtex,
    get_zotero_client,
)


class TestAttachmentDetails(unittest.TestCase):
    """Tests for AttachmentDetails dataclass."""

    def test_dataclass_creation(self):
        """AttachmentDetails stores all fields correctly."""
        att = AttachmentDetails(
            key="ABC123",
            title="Paper.pdf",
            filename="paper.pdf",
            content_type="application/pdf",
        )
        self.assertEqual(att.key, "ABC123")
        self.assertEqual(att.title, "Paper.pdf")
        self.assertEqual(att.filename, "paper.pdf")
        self.assertEqual(att.content_type, "application/pdf")


class TestFormatItemMetadata(unittest.TestCase):
    """Tests for format_item_metadata function."""

    def test_basic_fields(self):
        """Basic item with title, type, and key."""
        item = {
            "data": {
                "title": "Test Article",
                "itemType": "journalArticle",
                "key": "ABC123",
            }
        }
        result = format_item_metadata(item)
        self.assertIn("# Test Article", result)
        self.assertIn("**Type:** journalArticle", result)
        self.assertIn("**Key:** ABC123", result)

    def test_journal_article_with_publication_info(self):
        """Journal article includes publication details."""
        item = {
            "data": {
                "title": "Test Article",
                "itemType": "journalArticle",
                "key": "ABC123",
                "publicationTitle": "Nature",
                "volume": "10",
                "issue": "5",
                "pages": "100-110",
            }
        }
        result = format_item_metadata(item)
        self.assertIn("**Journal:** Nature", result)
        self.assertIn("Vol. 10", result)
        self.assertIn("No. 5", result)
        self.assertIn("pp. 100-110", result)

    def test_book_with_publisher(self):
        """Book includes publisher information."""
        item = {
            "data": {
                "title": "Test Book",
                "itemType": "book",
                "key": "ABC123",
                "publisher": "Academic Press",
                "place": "New York",
            }
        }
        result = format_item_metadata(item)
        self.assertIn("**Publisher:** Academic Press", result)
        self.assertIn("New York", result)

    def test_with_abstract_included(self):
        """Abstract is included when include_abstract=True."""
        item = {
            "data": {
                "title": "Test",
                "itemType": "article",
                "key": "ABC123",
                "abstractNote": "This is the abstract.",
            }
        }
        result = format_item_metadata(item, include_abstract=True)
        self.assertIn("## Abstract", result)
        self.assertIn("This is the abstract.", result)

    def test_without_abstract(self):
        """Abstract is excluded when include_abstract=False."""
        item = {
            "data": {
                "title": "Test",
                "itemType": "article",
                "key": "ABC123",
                "abstractNote": "This is the abstract.",
            }
        }
        result = format_item_metadata(item, include_abstract=False)
        self.assertNotIn("## Abstract", result)
        self.assertNotIn("This is the abstract.", result)

    def test_with_tags(self):
        """Tags are formatted as backtick-enclosed list."""
        item = {
            "data": {
                "title": "Test",
                "itemType": "article",
                "key": "ABC123",
                "tags": [{"tag": "machine-learning"}, {"tag": "AI"}],
            }
        }
        result = format_item_metadata(item)
        self.assertIn("`machine-learning`", result)
        self.assertIn("`AI`", result)

    def test_empty_data(self):
        """Empty data returns sensible defaults."""
        item = {"data": {}}
        result = format_item_metadata(item)
        self.assertIn("# Untitled", result)
        self.assertIn("**Type:** unknown", result)


class TestGenerateBibtex(unittest.TestCase):
    """Tests for generate_bibtex function."""

    def test_journal_article(self):
        """Journal article generates @article entry."""
        item = {
            "data": {
                "title": "Test Article",
                "itemType": "journalArticle",
                "key": "ABC123",
                "publicationTitle": "Nature",
                "volume": "10",
                "date": "2024-01-15",
                "creators": [
                    {"creatorType": "author", "firstName": "John", "lastName": "Smith"}
                ],
            }
        }
        result = generate_bibtex(item)
        self.assertTrue(result.startswith("@article{"))
        self.assertIn("title = {Test Article}", result)
        self.assertIn("journal = {Nature}", result)
        self.assertIn("volume = {10}", result)
        self.assertIn("year = {2024}", result)
        self.assertIn("author = {Smith, John}", result)

    def test_book(self):
        """Book generates @book entry."""
        item = {
            "data": {
                "title": "Test Book",
                "itemType": "book",
                "key": "ABC123",
                "publisher": "Academic Press",
                "date": "2023",
                "creators": [
                    {"creatorType": "author", "firstName": "Jane", "lastName": "Doe"}
                ],
            }
        }
        result = generate_bibtex(item)
        self.assertTrue(result.startswith("@book{"))
        self.assertIn("publisher = {Academic Press}", result)

    def test_slim_mode_excludes_abstract(self):
        """Slim mode (default) excludes abstract field."""
        item = {
            "data": {
                "title": "Test",
                "itemType": "journalArticle",
                "key": "ABC123",
                "abstractNote": "Long abstract text...",
                "creators": [],
            }
        }
        result = generate_bibtex(item, slim=True)
        self.assertNotIn("abstract =", result)

    def test_full_mode_includes_abstract(self):
        """Full mode includes abstract field."""
        item = {
            "data": {
                "title": "Test",
                "itemType": "journalArticle",
                "key": "ABC123",
                "abstractNote": "Long abstract text...",
                "creators": [],
            }
        }
        result = generate_bibtex(item, slim=False)
        self.assertIn("abstract = {Long abstract text...}", result)

    def test_escapes_braces(self):
        """Braces in field values are escaped."""
        item = {
            "data": {
                "title": "Test {with} braces",
                "itemType": "journalArticle",
                "key": "ABC123",
                "creators": [],
            }
        }
        result = generate_bibtex(item)
        self.assertIn("title = {Test \\{with\\} braces}", result)

    def test_raises_for_attachment(self):
        """Raises ValueError for attachment type."""
        item = {"data": {"itemType": "attachment", "key": "ABC123"}}
        with self.assertRaises(ValueError) as ctx:
            generate_bibtex(item)
        self.assertIn("attachment", str(ctx.exception))

    def test_raises_for_note(self):
        """Raises ValueError for note type."""
        item = {"data": {"itemType": "note", "key": "ABC123"}}
        with self.assertRaises(ValueError) as ctx:
            generate_bibtex(item)
        self.assertIn("note", str(ctx.exception))

    def test_no_date_uses_nodate(self):
        """Missing date uses 'nodate' in citation key."""
        item = {
            "data": {
                "title": "Test",
                "itemType": "journalArticle",
                "key": "ABC123",
                "creators": [{"creatorType": "author", "lastName": "Smith"}],
            }
        }
        result = generate_bibtex(item)
        self.assertIn("Smithnodate_ABC123", result)
        self.assertNotIn("year =", result)

    def test_multiple_authors(self):
        """Multiple authors joined with 'and'."""
        item = {
            "data": {
                "title": "Test",
                "itemType": "journalArticle",
                "key": "ABC123",
                "creators": [
                    {"creatorType": "author", "firstName": "John", "lastName": "Smith"},
                    {"creatorType": "author", "firstName": "Jane", "lastName": "Doe"},
                ],
            }
        }
        result = generate_bibtex(item)
        self.assertIn("author = {Smith, John and Doe, Jane}", result)


class TestGetZoteroClient(unittest.TestCase):
    """Tests for get_zotero_client function."""

    @patch.dict("os.environ", {}, clear=True)
    @patch("zotero_mcp.client.zotero.Zotero")
    def test_creates_local_client(self, mock_zotero):
        """Always creates client with local=True and default library_id."""
        get_zotero_client()
        mock_zotero.assert_called_once()
        call_kwargs = mock_zotero.call_args[1]
        self.assertTrue(call_kwargs["local"])
        self.assertIsNone(call_kwargs["api_key"])
        self.assertEqual(call_kwargs["library_id"], "0")
        self.assertEqual(call_kwargs["library_type"], "user")

    @patch.dict("os.environ", {"ZOTERO_LIBRARY_ID": "12345", "ZOTERO_LIBRARY_TYPE": "group"}, clear=True)
    @patch("zotero_mcp.client.zotero.Zotero")
    def test_respects_custom_library_config(self, mock_zotero):
        """Respects custom ZOTERO_LIBRARY_ID and ZOTERO_LIBRARY_TYPE."""
        get_zotero_client()
        mock_zotero.assert_called_once()
        call_kwargs = mock_zotero.call_args[1]
        self.assertTrue(call_kwargs["local"])
        self.assertEqual(call_kwargs["library_id"], "12345")
        self.assertEqual(call_kwargs["library_type"], "group")



if __name__ == "__main__":
    unittest.main()
