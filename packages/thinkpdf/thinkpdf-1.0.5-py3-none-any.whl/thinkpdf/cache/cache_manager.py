"""
Cache Manager - Intelligent caching for PDF conversions.

Avoids re-processing PDFs that haven't changed, saving time
and computational resources.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class CacheEntry:
    """A cached conversion result."""

    file_hash: str
    file_path: str
    file_size: int
    conversion_time: str
    options_hash: str
    markdown_path: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        return cls(**data)


class CacheManager:
    """
    Manage cached PDF conversions.

    Features:
    - SHA256-based file hashing
    - Options-aware caching (different options = different cache)
    - Automatic cache invalidation on file changes
    - Configurable cache location
    - Cache size limits
    """

    DEFAULT_CACHE_DIR = Path.home() / ".thinkpdf" / "cache"
    INDEX_FILE = "cache_index.json"
    MAX_CACHE_SIZE_MB = 500

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or self.DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.cache_dir / self.INDEX_FILE
        self._index: Dict[str, CacheEntry] = {}
        self._load_index()

    def get_cached(
        self,
        pdf_path: str | Path,
        options_hash: Optional[str] = None,
    ) -> Optional[str]:
        """
        Get cached markdown if available.

        Args:
            pdf_path: Path to the PDF file
            options_hash: Hash of conversion options

        Returns:
            Cached markdown content or None if not cached
        """
        pdf_path = Path(pdf_path)
        cache_key = self._make_cache_key(pdf_path, options_hash)

        if cache_key not in self._index:
            return None

        entry = self._index[cache_key]

        current_hash = self._hash_file(pdf_path)
        if current_hash != entry.file_hash:
            self._remove_entry(cache_key)
            return None

        md_path = Path(entry.markdown_path)
        if not md_path.exists():
            self._remove_entry(cache_key)
            return None

        try:
            return md_path.read_text(encoding="utf-8")
        except OSError:
            self._remove_entry(cache_key)
            return None

    def cache(
        self,
        pdf_path: str | Path,
        markdown: str,
        options_hash: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Cache a conversion result.

        Args:
            pdf_path: Path to the original PDF
            markdown: Converted markdown content
            options_hash: Hash of conversion options
            metadata: Optional metadata to store
        """
        pdf_path = Path(pdf_path)
        cache_key = self._make_cache_key(pdf_path, options_hash)

        md_filename = f"{cache_key}.md"
        md_path = self.cache_dir / md_filename
        md_path.write_text(markdown, encoding="utf-8")

        entry = CacheEntry(
            file_hash=self._hash_file(pdf_path),
            file_path=str(pdf_path.absolute()),
            file_size=pdf_path.stat().st_size,
            conversion_time=datetime.now().isoformat(),
            options_hash=options_hash or "",
            markdown_path=str(md_path),
            metadata=metadata or {},
        )

        self._index[cache_key] = entry
        self._save_index()

        self._enforce_size_limit()

    def invalidate(self, pdf_path: str | Path) -> None:
        """Invalidate all cache entries for a PDF file."""
        pdf_path = Path(pdf_path)
        keys_to_remove = [
            key
            for key, entry in self._index.items()
            if Path(entry.file_path) == pdf_path.absolute()
        ]

        for key in keys_to_remove:
            self._remove_entry(key)

        self._save_index()

    def clear(self) -> None:
        """Clear all cached entries."""
        for key in list(self._index.keys()):
            self._remove_entry(key)

        self._index.clear()
        self._save_index()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_size = sum(
            Path(entry.markdown_path).stat().st_size
            for entry in self._index.values()
            if Path(entry.markdown_path).exists()
        )

        return {
            "entries": len(self._index),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "cache_dir": str(self.cache_dir),
        }

    def _make_cache_key(self, pdf_path: Path, options_hash: Optional[str]) -> str:
        """Create a unique cache key for a PDF + options combination."""
        key_str = str(pdf_path.absolute())
        if options_hash:
            key_str += f":{options_hash}"

        return hashlib.sha256(key_str.encode()).hexdigest()[:16]

    def _hash_file(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _remove_entry(self, cache_key: str) -> None:
        """Remove a cache entry and its markdown file."""
        if cache_key in self._index:
            entry = self._index[cache_key]
            md_path = Path(entry.markdown_path)
            if md_path.exists():
                md_path.unlink()
            del self._index[cache_key]

    def _load_index(self) -> None:
        """Load the cache index from disk."""
        if self.index_path.exists():
            try:
                data = json.loads(self.index_path.read_text(encoding="utf-8"))
                self._index = {
                    key: CacheEntry.from_dict(value) for key, value in data.items()
                }
            except (json.JSONDecodeError, KeyError):
                self._index = {}

    def _save_index(self) -> None:
        """Save the cache index to disk."""
        data = {key: entry.to_dict() for key, entry in self._index.items()}
        self.index_path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

    def _enforce_size_limit(self) -> None:
        """Remove oldest entries if cache exceeds size limit."""
        max_size_bytes = self.MAX_CACHE_SIZE_MB * 1024 * 1024

        entries_with_size = []
        for key, entry in self._index.items():
            md_path = Path(entry.markdown_path)
            if md_path.exists():
                size = md_path.stat().st_size
                entries_with_size.append((key, entry.conversion_time, size))

        total_size = sum(e[2] for e in entries_with_size)

        if total_size <= max_size_bytes:
            return

        entries_with_size.sort(key=lambda x: x[1])

        for key, _, size in entries_with_size:
            if total_size <= max_size_bytes:
                break

            self._remove_entry(key)
            total_size -= size

        self._save_index()
