"""Layout manager to place components within a row."""

from family_chart.svg_component import SvgComponent


class SvgRowLayout:
    """Layout manager to place components within a row."""

    PADDING = 20
    HSPACER = 40

    def __init__(self):
        """Default constructor."""
        self.components = []
        self.height = 0
        self.width = 0

    def add_component(self, c: SvgComponent):
        """Add component to the list."""
        self.components.append(c)

    def calculate_dimensions(self):
        """Calculate height and width."""
        self.height = max(c.height for c in self.components)
        self.width = SvgRowLayout.PADDING * 2 + sum(c.width for c in self.components)
        if len(self.components) > 1:
            self.width += SvgRowLayout.HSPACER * (len(self.components) - 1)

    def render(self, y: int = 0) -> str:
        """Return an SVG string with all components rendered in a row at the given y position."""
        self.calculate_dimensions()
        parts = []
        x = SvgRowLayout.PADDING
        for i, c in enumerate(self.components):
            cy = y + (self.height - c.height) // 2
            parts.append(c.render(x, cy))
            x += c.width
            if i < len(self.components) - 1:
                x += SvgRowLayout.HSPACER
        return "".join(parts)
