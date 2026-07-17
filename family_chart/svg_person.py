"""SVG rendering for family chart nodes."""

import struct

from family_chart.person import Person
from family_chart.svg_component import SvgComponent
from family_chart.text_line import TextLine


def image_dimensions(path: str) -> tuple[int, int] | None:
    """Return (width, height) of a PNG or JPEG file, or None if unreadable."""
    try:
        with open(path, "rb") as f:
            magic = f.read(8)
            if magic[:8] == b"\x89PNG\r\n\x1a\n":
                f.seek(16)
                w, h = struct.unpack(">II", f.read(8))
                return w, h
            if magic[:2] == b"\xff\xd8":
                f.seek(2)
                while True:
                    b = f.read(2)
                    if len(b) < 2 or b[0] != 0xFF:
                        break
                    marker = b[1]
                    if marker in (0xD8, 0xD9):
                        continue
                    seg_len = f.read(2)
                    if len(seg_len) < 2:
                        break
                    length = struct.unpack(">H", seg_len)[0]
                    if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                        f.read(1)  # precision byte
                        h, w = struct.unpack(">HH", f.read(4))
                        return w, h
                    f.seek(length - 2, 1)
    except (OSError, struct.error):
        # FIXME: VK: fix error handling
        pass
    return None


class SvgPerson(SvgComponent):
    """Renders family chart nodes as SVG elements."""

    def __init__(self, person: Person):
        """Default constructor."""
        super().__init__()
        self.person = person
        self.photo_width = SvgComponent.PHOTO_WIDTH
        if person.photo:
            dims = image_dimensions(person.photo)
            if dims:
                img_w, img_h = dims
                self.photo_width = round(SvgComponent.PHOTO_HEIGHT * img_w / img_h)
        text_width = (
            max(
                SvgComponent.MIN_WIDTH,
                max(len(e.text) * (SvgComponent.FONT_SIZE * 0.5) for e in person.text_lines) + SvgComponent.PADDING * 2,
            )
            if person.text_lines
            else SvgComponent.MIN_WIDTH
        )
        photo_section_height = (SvgComponent.PHOTO_HEIGHT + SvgComponent.PADDING) if person.photo else 0
        self.width = max(text_width, self.photo_width + SvgComponent.PADDING * 2) if person.photo else text_width
        self.height = (
            SvgComponent.PADDING * 2 + photo_section_height + len(person.text_lines) * SvgComponent.LINE_HEIGHT
        )

    def render(self, x: int = 0, y: int = 0) -> str:
        """Return an SVG snippet for a Person as a labeled rectangle."""
        fill = self.escape_text(self.person.fillcolor) if self.person.fillcolor else "#ffffff"
        photo_section_height = (SvgComponent.PHOTO_HEIGHT + SvgComponent.PADDING) if self.person.photo else 0
        photo_el = ""
        if self.person.photo:
            photo_x = x + SvgComponent.PADDING + int(self.width - self.photo_width) // 2
            photo_y = y + SvgComponent.PADDING
            photo_el = (
                f'<image x="{photo_x}" y="{photo_y}" width="{self.photo_width}" '
                f'height="{SvgComponent.PHOTO_HEIGHT}" href="{self.escape_text(self.person.photo)}"/>\n'
            )
        text_els = "\n".join(
            self.render_peron_text_line(
                e,
                x + SvgComponent.PADDING,
                y + SvgComponent.PADDING + photo_section_height + (i + 1) * SvgComponent.LINE_HEIGHT - 3,
            )
            for i, e in enumerate(self.person.text_lines)
        )
        return (
            f'<rect x="{x}" y="{y}" width="{self.width:.0f}" height="{self.height}" '
            f'fill="{fill}" stroke="#000000" stroke-width="1"/>\n'
            f"{photo_el}"
            f"{text_els}"
        )

    def render_peron_text_line(self, text_line: TextLine, x: int, y: int) -> str:
        """Return all text_lines rendered on separate lines augmented with clickable links where needed."""
        url = self.safe_url(text_line.map_url) if text_line.map_url else None
        text = (
            f'  <text x="{x}" y="{y}" font-family="sans-serif" font-size="{SvgComponent.FONT_SIZE}" '
            f'fill="{"#0000EE" if url else "#000000"}">{self.escape_text(text_line.text)}</text>'
        )
        if url:
            return f'  <a href="{self.escape_text(url)}" target="_blank">\n  {text}\n  </a>'
        return text
