"""
Local Zotero database reader for direct SQLite access.

Provides read-only access to Zotero's local SQLite database for fast
annotation retrieval without going through the API.
"""

import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Annotation:
    """Represents a PDF annotation from Zotero."""
    type: str
    text: Optional[str]
    comment: Optional[str]
    color: Optional[str]
    page_label: Optional[str]
    attachment_name: Optional[str]
    parent_key: Optional[str] = None
    parent_title: Optional[str] = None


# Zotero annotation type codes (from itemAnnotations table)
ANNOTATION_TYPE_MAP = {
    1: "highlight",
    2: "note",
    3: "image",
    4: "ink",
    5: "underline",
    6: "text",
}


def _parse_annotation_type(raw_type) -> str:
    """Convert Zotero annotation type (int or str) to string label."""
    if isinstance(raw_type, int):
        return ANNOTATION_TYPE_MAP.get(raw_type, "highlight")
    if isinstance(raw_type, str):
        return raw_type
    return "highlight"


class LocalZoteroDB:
    """
    Read-only SQLite reader for Zotero's local database.
    
    Provides fast access to annotations without API overhead.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database reader.
        
        Args:
            db_path: Optional path to zotero.sqlite. Auto-detects if None.
        """
        self.db_path = Path(db_path) if db_path else self._find_zotero_db()
        self._connection: Optional[sqlite3.Connection] = None

    def _find_zotero_db(self) -> Path:
        """
        Auto-detect Zotero database location.
        
        Supports multiple platforms and environment variable override.
        
        Environment variables:
            ZOTERO_DATABASE_PATH: Direct path to zotero.sqlite
            ZOTERO_DATA_DIR: Path to Zotero data directory
        
        Returns:
            Path to zotero.sqlite file.
            
        Raises:
            FileNotFoundError: If database cannot be located.
        """
        # 1. Environment variable: direct database path
        if env_db_path := os.getenv("ZOTERO_DATABASE_PATH"):
            path = Path(env_db_path)
            if path.exists():
                return path
            raise FileNotFoundError(
                f"ZOTERO_DATABASE_PATH set but file not found: {env_db_path}"
            )
        
        # 2. Environment variable: data directory
        if env_data_dir := os.getenv("ZOTERO_DATA_DIR"):
            path = Path(env_data_dir) / "zotero.sqlite"
            if path.exists():
                return path
            raise FileNotFoundError(
                f"ZOTERO_DATA_DIR set but database not found: {path}"
            )
        
        # 3. Platform-specific auto-detection
        candidates = self._get_platform_candidates()
        
        for candidate in candidates:
            if candidate.exists():
                return candidate
        
        # Build helpful error message
        searched = "\n  - ".join(str(c) for c in candidates)
        raise FileNotFoundError(
            f"Zotero database not found. Searched locations:\n  - {searched}\n"
            "Set ZOTERO_DATA_DIR or ZOTERO_DATABASE_PATH environment variable "
            "to specify a custom location."
        )
    
    def _get_platform_candidates(self) -> list[Path]:
        """
        Get platform-specific candidate paths for Zotero database.
        
        Returns:
            List of paths to check, in priority order.
        """
        home = Path.home()
        candidates = []
        
        # Zotero 7+ default location (all platforms)
        candidates.append(home / "Zotero" / "zotero.sqlite")
        
        if sys.platform == "win32":
            # Windows: AppData location
            appdata = os.getenv("APPDATA")
            if appdata:
                candidates.append(Path(appdata) / "Zotero" / "Zotero" / "zotero.sqlite")
        
        elif sys.platform == "linux":
            # Linux: .zotero profile directory (Zotero 6 and earlier)
            zotero_dir = home / ".zotero" / "zotero"
            if zotero_dir.exists():
                # Find profile directories (e.g., abc123.default)
                for profile_dir in zotero_dir.iterdir():
                    if profile_dir.is_dir():
                        db_path = profile_dir / "zotero.sqlite"
                        candidates.append(db_path)
            
            # Snap/Flatpak locations
            candidates.append(home / "snap" / "zotero-snap" / "common" / "Zotero" / "zotero.sqlite")
        
        elif sys.platform == "darwin":
            # macOS: standard location is ~/Zotero (already added above)
            pass
        
        return candidates

    def _get_connection(self) -> sqlite3.Connection:
        """Get read-only database connection with no-lock mode."""
        if self._connection is None:
            # mode=ro: read-only, nolock=1: avoid "database is locked" when Zotero is running
            uri = f"file:{self.db_path}?mode=ro&nolock=1"
            self._connection = sqlite3.connect(uri, uri=True)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def get_data_directory(self) -> Path:
        """Return the Zotero data directory (parent of database)."""
        return self.db_path.parent

    def resolve_storage_path(self, storage_path: str) -> Optional[Path]:
        """
        Convert Zotero storage: path to actual filesystem path.
        
        Args:
            storage_path: Path like 'storage:ABCDEF12/paper.pdf'
            
        Returns:
            Resolved filesystem path, or None if invalid.
        """
        if not storage_path or not storage_path.startswith("storage:"):
            return None
        
        rel_path = storage_path.replace("storage:", "", 1)
        resolved = self.get_data_directory() / "storage" / rel_path
        
        return resolved if resolved.exists() else None

    def get_annotations_for_item(self, item_key: str) -> list[Annotation]:
        """
        Get all PDF annotations for a Zotero item.
        
        Uses three-level join: Item -> Attachment -> Annotation
        
        Args:
            item_key: The Zotero item key.
            
        Returns:
            List of Annotation objects.
        """
        conn = self._get_connection()
        
        query = """
        SELECT 
            ia.type,
            ia.text,
            ia.comment,
            ia.color,
            ia.pageLabel,
            iatt.path AS attachmentPath
        FROM itemAnnotations ia
        JOIN items att ON ia.parentItemID = att.itemID
        JOIN itemAttachments iatt ON att.itemID = iatt.itemID
        JOIN items parent ON iatt.parentItemID = parent.itemID
        WHERE parent.key = ?
          AND iatt.contentType = 'application/pdf'
          AND (iatt.path IS NULL OR iatt.path NOT LIKE '%snapshot%')
        ORDER BY att.itemID, ia.sortIndex
        """
        
        cursor = conn.execute(query, (item_key,))
        annotations = []
        
        for row in cursor:
            attachment_name = None
            if row["attachmentPath"]:
                path = row["attachmentPath"]
                if path.startswith("storage:"):
                    parts = path.replace("storage:", "").split("/")
                    attachment_name = parts[-1] if parts else None
            
            annotations.append(Annotation(
                type=_parse_annotation_type(row["type"]),
                text=row["text"],
                comment=row["comment"],
                color=row["color"],
                page_label=row["pageLabel"],
                attachment_name=attachment_name
            ))
        
        return annotations

    def search_annotations(self, query: str, limit: int = 50) -> list[Annotation]:
        """
        Search all PDF annotations across the library by keyword.
        
        Searches both highlighted text and user comments.
        
        Args:
            query: Search keyword (case-insensitive).
            limit: Maximum results to return.
            
        Returns:
            List of Annotation objects with parent paper info.
        """
        conn = self._get_connection()
        
        search_pattern = f"%{query}%"
        
        sql = """
        SELECT 
            ia.type,
            ia.text,
            ia.comment,
            ia.color,
            ia.pageLabel,
            iatt.path AS attachmentPath,
            parent.key AS parentKey,
            (SELECT value FROM itemData id
             JOIN itemDataValues idv ON id.valueID = idv.valueID
             JOIN fields f ON id.fieldID = f.fieldID
             WHERE id.itemID = parent.itemID AND f.fieldName = 'title'
            ) AS parentTitle
        FROM itemAnnotations ia
        JOIN items att ON ia.parentItemID = att.itemID
        JOIN itemAttachments iatt ON att.itemID = iatt.itemID
        JOIN items parent ON iatt.parentItemID = parent.itemID
        WHERE (ia.text LIKE ? OR ia.comment LIKE ?)
          AND iatt.contentType = 'application/pdf'
        ORDER BY parent.itemID, ia.sortIndex
        LIMIT ?
        """
        
        cursor = conn.execute(sql, (search_pattern, search_pattern, limit))
        annotations = []
        
        for row in cursor:
            attachment_name = None
            if row["attachmentPath"]:
                path = row["attachmentPath"]
                if path.startswith("storage:"):
                    parts = path.replace("storage:", "").split("/")
                    attachment_name = parts[-1] if parts else None
            
            annotations.append(Annotation(
                type=_parse_annotation_type(row["type"]),
                text=row["text"],
                comment=row["comment"],
                color=row["color"],
                page_label=row["pageLabel"],
                attachment_name=attachment_name,
                parent_key=row["parentKey"],
                parent_title=row["parentTitle"],
            ))
        
        return annotations

    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def get_local_db() -> Optional[LocalZoteroDB]:
    """
    Get a LocalZoteroDB instance if available.
    
    Returns:
        LocalZoteroDB instance if database exists, None otherwise.
    """
    try:
        return LocalZoteroDB()
    except FileNotFoundError:
        return None
