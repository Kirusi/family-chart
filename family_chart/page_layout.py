"""Layout manager to arrange rows on a page."""

from family_chart.svg_row_layout import SvgRowLayout


class PageLayout:
    """Layout manager to arrange rows on a page."""

    PADDING = 20
    VSPACER = 60

    def __init__(self):
        """Default constructor."""
        self.rows = []
        self.height = 0
        self.width = 0

    def add_row(self, row: SvgRowLayout):
        """Add a row to the page."""
        self.rows.append(row)

    def calculate_dimensions(self):
        """Calculate height and width."""
        for row in self.rows:
            row.calculate_dimensions()
        self.height = PageLayout.PADDING * 2 + sum(r.height for r in self.rows)
        if len(self.rows) > 1:
            self.height += PageLayout.VSPACER * (len(self.rows) - 1)
        self.width = max(r.width for r in self.rows)

    def render(self) -> str:
        """Return an SVG string with all rows rendered on the page."""
        self.calculate_dimensions()
        parts = []
        y = PageLayout.PADDING
        for i, row in enumerate(self.rows):
            parts.append(row.render(y))
            y += row.height
            if i < len(self.rows) - 1:
                y += PageLayout.VSPACER
        return "".join(parts)
