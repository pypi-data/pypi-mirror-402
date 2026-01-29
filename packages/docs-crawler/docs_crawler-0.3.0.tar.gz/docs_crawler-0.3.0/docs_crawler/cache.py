"""Cache module for incremental crawling support."""

import os
import json
import hashlib
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

CACHE_VERSION = 1
CACHE_FILENAME = ".docs-crawler-cache.json"


class CrawlCache:
    """
    Manages cache for incremental crawling.

    Stores metadata about crawled pages to detect changes:
    - URL
    - Content hash (MD5)
    - Last crawl timestamp
    - ETag and Last-Modified headers (if available)
    """

    def __init__(self, cache_dir):
        """
        Initialize the cache.

        Args:
            cache_dir: Directory to store the cache file
        """
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, CACHE_FILENAME)
        self.data = self._load_cache()

    def _load_cache(self):
        """Load cache from disk."""
        if not os.path.exists(self.cache_file):
            return {"version": CACHE_VERSION, "pages": {}}

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check version compatibility
            if data.get("version") != CACHE_VERSION:
                logger.warning("Cache version mismatch, creating new cache")
                return {"version": CACHE_VERSION, "pages": {}}

            return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load cache: {e}")
            return {"version": CACHE_VERSION, "pages": {}}

    def save(self):
        """Save cache to disk."""
        os.makedirs(self.cache_dir, exist_ok=True)
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Cache saved to {self.cache_file}")
        except IOError as e:
            logger.error(f"Failed to save cache: {e}")

    @staticmethod
    def compute_hash(content):
        """Compute MD5 hash of content."""
        if isinstance(content, str):
            content = content.encode("utf-8")
        return hashlib.md5(content).hexdigest()

    def get_page_info(self, url):
        """
        Get cached info for a URL.

        Args:
            url: The URL to look up

        Returns:
            dict or None: Cached page info or None if not cached
        """
        return self.data["pages"].get(url)

    def update_page(self, url, content_hash, etag=None, last_modified=None):
        """
        Update cache entry for a URL.

        Args:
            url: The URL
            content_hash: MD5 hash of the markdown content
            etag: ETag header value (optional)
            last_modified: Last-Modified header value (optional)
        """
        self.data["pages"][url] = {
            "content_hash": content_hash,
            "last_crawled": datetime.now().isoformat(),
            "etag": etag,
            "last_modified": last_modified,
        }

    def is_changed(self, url, new_content_hash):
        """
        Check if a page has changed since last crawl.

        Args:
            url: The URL to check
            new_content_hash: Hash of the new content

        Returns:
            bool: True if changed or not in cache, False if unchanged
        """
        cached = self.get_page_info(url)
        if not cached:
            return True
        return cached.get("content_hash") != new_content_hash

    def remove_page(self, url):
        """Remove a URL from cache."""
        if url in self.data["pages"]:
            del self.data["pages"][url]

    def get_cached_urls(self):
        """Get all cached URLs."""
        return set(self.data["pages"].keys())

    def get_stats(self):
        """Get cache statistics."""
        return {
            "total_pages": len(self.data["pages"]),
            "cache_file": self.cache_file,
        }

    def clear(self):
        """Clear all cache data."""
        self.data = {"version": CACHE_VERSION, "pages": {}}
        logger.info("Cache cleared")
