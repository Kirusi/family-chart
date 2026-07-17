"""Render family object."""

from family_chart.family import Family
from family_chart.svg_component import SvgComponent
from family_chart.text_line import TextLine


class SvgFamily(SvgComponent):
    """Render family object."""

    def __init__(self, family: Family):
        """Default constructor."""
        super().__init__()
        self.family = family
        self.width = (
            max(
                SvgComponent.MIN_WIDTH,
                max(len(e.text) * (SvgComponent.FONT_SIZE * 0.5) for e in family.text_lines) + SvgComponent.PADDING * 2,
            )
            if family.text_lines
            else SvgComponent.MIN_WIDTH
        )
        self.height = SvgComponent.PADDING * 2 + len(family.text_lines) * SvgComponent.LINE_HEIGHT

    @property
    def id(self):
        """Return family ID."""
        return self.family.id

    def render(self, x: int = 0, y: int = 0):
        """Render family details."""
        """Return an SVG snippet for a Family as a labeled ellipse."""
        fill = self.escape_text(self.family.fillcolor) if self.family.fillcolor else "#ffffff"
        text_lines = self.family.text_lines
        rx = self.width / 2
        ry = self.height / 2
        cx, cy = x + rx, y + ry
        y_offset = (len(text_lines) - 1) / 2 * SvgComponent.LINE_HEIGHT
        text_els = "\n".join(
            self.render_family_text_line(e, cx, cy - y_offset + i * SvgComponent.LINE_HEIGHT)
            for i, e in enumerate(text_lines)
        )
        return (
            f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" '
            f'fill="{fill}" stroke="#000000" stroke-width="1"/>\n'
            f"{text_els}"
        )

    def render_family_text_line(self, text_line: TextLine, cx: float, cy: float) -> str:
        """Render one text line in a family object."""
        url = self.safe_url(text_line.map_url) if text_line.map_url else None
        text = (
            f'<text x="{cx:.0f}" y="{cy:.0f}" text-anchor="middle" '
            f'font-family="sans-serif" font-size="{SvgComponent.FONT_SIZE}" '
            f'fill="#000000">{self.escape_text(text_line.text)}</text>'
        )
        if url:
            return f'  <a href="{self.escape_text(url)}" target="_blank">\n  {text}\n  </a>'
        return text
