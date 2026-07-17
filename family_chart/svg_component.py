"""Shared component for Person and Family renderings."""


class SvgComponent:
    """Shared component for Person and Family renderings."""

    PADDING = 8
    LINE_HEIGHT = 16
    FONT_SIZE = 12
    MIN_WIDTH = 120
    PHOTO_WIDTH = 80
    PHOTO_HEIGHT = 80

    SAFE_URL_SCHEMES = ("http://", "https://")

    def escape_text(self, text: str) -> str:
        """Replace characters that may cause problem when used in XML notation."""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    def safe_url(self, url: str) -> str | None:
        """Return the URL if it uses an allowed scheme, else None."""
        return url if url.lower().startswith(SvgComponent.SAFE_URL_SCHEMES) else None
