"""Server favicon handling for MCPulse."""

import base64
import io
from typing import Optional, Tuple

from PIL import Image


class FaviconHandler:
    """Handler for Minecraft server favicons."""

    def __init__(self):
        self._cache: dict = {}

    def parse_favicon(self, favicon_data: Optional[str]) -> Optional[bytes]:
        """Parse favicon from base64 data URI format."""
        if not favicon_data:
            return None
        try:
            if favicon_data.startswith("data:"):
                _, base64_data = favicon_data.split(",", 1)
            else:
                base64_data = favicon_data
            return base64.b64decode(base64_data)
        except Exception:
            return None

    def resize_favicon(
        self,
        image_bytes: bytes,
        size: Tuple[int, int] = (64, 64),
    ) -> bytes:
        """Resize favicon to specified size."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image = image.resize(size, Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            image.save(buf, format='PNG')
            buf.seek(0)
            return buf.getvalue()
        except Exception:
            return image_bytes

    def get_favicon(
        self, server_address: str, favicon_data: Optional[str]
    ) -> Optional[bytes]:
        """Get favicon with caching."""
        if server_address in self._cache:
            return self._cache[server_address]
        favicon = self.parse_favicon(favicon_data)
        if favicon:
            favicon = self.resize_favicon(favicon)
            self._cache[server_address] = favicon
        return favicon

    def clear_cache(self):
        """Clear the favicon cache."""
        self._cache.clear()
