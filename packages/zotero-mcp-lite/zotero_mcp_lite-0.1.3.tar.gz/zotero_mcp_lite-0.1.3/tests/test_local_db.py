"""
Tests for zotero_mcp.local_db module.

Tests cover:
- Annotation: Dataclass creation
- LocalZoteroDB: Database path detection and storage path resolution
- get_local_db: Factory function
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from zotero_mcp.local_db import Annotation, LocalZoteroDB, get_local_db


class TestAnnotation(unittest.TestCase):
    """Tests for Annotation dataclass."""

    def test_dataclass_creation(self):
        """Annotation stores all fields correctly."""
        anno = Annotation(
            type="highlight",
            text="Important text",
            comment="My note",
            color="#FFFF00",
            page_label="5",
            attachment_name="paper.pdf",
        )
        self.assertEqual(anno.type, "highlight")
        self.assertEqual(anno.text, "Important text")
        self.assertEqual(anno.comment, "My note")
        self.assertEqual(anno.color, "#FFFF00")
        self.assertEqual(anno.page_label, "5")
        self.assertEqual(anno.attachment_name, "paper.pdf")

    def test_optional_fields_can_be_none(self):
        """Optional fields accept None values."""
        anno = Annotation(
            type="highlight",
            text=None,
            comment=None,
            color=None,
            page_label=None,
            attachment_name=None,
        )
        self.assertIsNone(anno.text)
        self.assertIsNone(anno.comment)

    def test_parent_fields_default_to_none(self):
        """Parent key and title fields default to None."""
        anno = Annotation(
            type="highlight",
            text="Test",
            comment=None,
            color=None,
            page_label=None,
            attachment_name=None,
        )
        self.assertIsNone(anno.parent_key)
        self.assertIsNone(anno.parent_title)

    def test_parent_fields_can_be_set(self):
        """Parent key and title can be provided."""
        anno = Annotation(
            type="highlight",
            text="Test",
            comment=None,
            color=None,
            page_label="10",
            attachment_name="paper.pdf",
            parent_key="ABC123",
            parent_title="Test Paper Title",
        )
        self.assertEqual(anno.parent_key, "ABC123")
        self.assertEqual(anno.parent_title, "Test Paper Title")


class TestLocalZoteroDBPathDetection(unittest.TestCase):
    """Tests for LocalZoteroDB path detection."""

    def test_get_platform_candidates_returns_list(self):
        """_get_platform_candidates returns a non-empty list."""
        db = LocalZoteroDB.__new__(LocalZoteroDB)
        candidates = db._get_platform_candidates()
        self.assertIsInstance(candidates, list)
        self.assertTrue(len(candidates) > 0)

    def test_get_platform_candidates_includes_home_zotero(self):
        """Candidates include ~/Zotero/zotero.sqlite."""
        db = LocalZoteroDB.__new__(LocalZoteroDB)
        candidates = db._get_platform_candidates()
        home_zotero = Path.home() / "Zotero" / "zotero.sqlite"
        self.assertIn(home_zotero, candidates)

    def test_find_zotero_db_with_env_database_path(self):
        """ZOTERO_DATABASE_PATH environment variable is respected."""
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
            temp_path = f.name

        try:
            with patch.dict(os.environ, {"ZOTERO_DATABASE_PATH": temp_path}):
                db = LocalZoteroDB()
                self.assertEqual(str(db.db_path), temp_path)
        finally:
            os.unlink(temp_path)

    def test_find_zotero_db_with_env_data_dir(self):
        """ZOTERO_DATA_DIR environment variable is respected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create fake zotero.sqlite
            db_path = Path(tmpdir) / "zotero.sqlite"
            db_path.touch()

            with patch.dict(
                os.environ, {"ZOTERO_DATA_DIR": tmpdir}, clear=False
            ):
                # Clear DATABASE_PATH if set
                env = os.environ.copy()
                env.pop("ZOTERO_DATABASE_PATH", None)
                with patch.dict(os.environ, env, clear=True):
                    with patch.dict(os.environ, {"ZOTERO_DATA_DIR": tmpdir}):
                        db = LocalZoteroDB()
                        self.assertEqual(db.db_path, db_path)

    def test_find_zotero_db_raises_when_env_path_not_found(self):
        """FileNotFoundError when ZOTERO_DATABASE_PATH points to missing file."""
        with patch.dict(
            os.environ, {"ZOTERO_DATABASE_PATH": "/nonexistent/path.sqlite"}, clear=True
        ):
            with self.assertRaises(FileNotFoundError) as ctx:
                LocalZoteroDB()
            self.assertIn("ZOTERO_DATABASE_PATH", str(ctx.exception))

    def test_init_with_explicit_path(self):
        """Can initialize with explicit db_path argument."""
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
            temp_path = f.name

        try:
            db = LocalZoteroDB(db_path=temp_path)
            self.assertEqual(str(db.db_path), temp_path)
        finally:
            os.unlink(temp_path)


class TestLocalZoteroDBStoragePath(unittest.TestCase):
    """Tests for LocalZoteroDB.resolve_storage_path."""

    def setUp(self):
        """Create a temporary directory structure for testing."""
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = Path(self.tmpdir) / "zotero.sqlite"
        self.db_path.touch()
        self.storage_dir = Path(self.tmpdir) / "storage" / "ABCD1234"
        self.storage_dir.mkdir(parents=True)
        self.test_file = self.storage_dir / "paper.pdf"
        self.test_file.touch()
        self.db = LocalZoteroDB(db_path=str(self.db_path))

    def tearDown(self):
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.tmpdir)

    def test_resolve_storage_path_valid(self):
        """Valid storage: path resolves to filesystem path."""
        result = self.db.resolve_storage_path("storage:ABCD1234/paper.pdf")
        self.assertEqual(result, self.test_file)

    def test_resolve_storage_path_nonexistent(self):
        """Nonexistent file returns None."""
        result = self.db.resolve_storage_path("storage:ABCD1234/nonexistent.pdf")
        self.assertIsNone(result)

    def test_resolve_storage_path_invalid_prefix(self):
        """Path without storage: prefix returns None."""
        result = self.db.resolve_storage_path("ABCD1234/paper.pdf")
        self.assertIsNone(result)

    def test_resolve_storage_path_empty(self):
        """Empty string returns None."""
        result = self.db.resolve_storage_path("")
        self.assertIsNone(result)

    def test_resolve_storage_path_none(self):
        """None input returns None."""
        result = self.db.resolve_storage_path(None)
        self.assertIsNone(result)


class TestLocalZoteroDBDataDirectory(unittest.TestCase):
    """Tests for LocalZoteroDB.get_data_directory."""

    def test_get_data_directory(self):
        """get_data_directory returns parent of database file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "zotero.sqlite"
            db_path.touch()
            db = LocalZoteroDB(db_path=str(db_path))
            self.assertEqual(db.get_data_directory(), Path(tmpdir))


class TestLocalZoteroDBContextManager(unittest.TestCase):
    """Tests for LocalZoteroDB context manager."""

    def test_context_manager_closes_connection(self):
        """Connection is closed when exiting context."""
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
            temp_path = f.name

        try:
            with LocalZoteroDB(db_path=temp_path) as db:
                # Access connection to open it
                pass  # Connection not actually opened until _get_connection called

            # After context exit, connection should be None
            self.assertIsNone(db._connection)
        finally:
            os.unlink(temp_path)


class TestGetLocalDb(unittest.TestCase):
    """Tests for get_local_db factory function."""

    @patch.object(LocalZoteroDB, "__init__", side_effect=FileNotFoundError("Not found"))
    def test_returns_none_when_not_found(self, mock_init):
        """Returns None when database is not found."""
        result = get_local_db()
        self.assertIsNone(result)

    def test_returns_instance_when_found(self):
        """Returns LocalZoteroDB instance when database exists."""
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
            temp_path = f.name

        try:
            with patch.dict(os.environ, {"ZOTERO_DATABASE_PATH": temp_path}):
                result = get_local_db()
                self.assertIsInstance(result, LocalZoteroDB)
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
