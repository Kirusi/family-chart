import struct

from family_chart.person import Person
from family_chart.svg_component import SvgComponent
from family_chart.svg_person import SvgPerson, image_dimensions
from family_chart.text_line import TextLine


def make_person(id="I0001", fillcolor=None, photo=None, text_lines=None, all_marriages=None):
    return Person(
        id=id, fillcolor=fillcolor, photo=photo, text_lines=text_lines or [], all_marriages=all_marriages or []
    )


def png_bytes(width: int, height: int) -> bytes:
    magic = b"\x89PNG\r\n\x1a\n"
    ihdr_header = b"\x00\x00\x00\r" + b"IHDR"
    return magic + ihdr_header + struct.pack(">II", width, height)


def jpeg_bytes(width: int, height: int) -> bytes:
    soi = b"\xff\xd8"
    # APP0 segment: 2 bytes marker + 2 bytes length (16) + 14 bytes content
    app0_content = b"\x4a\x46\x49\x46\x00" + b"\x00" * 9
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + app0_content
    # SOF0 segment: precision (1) + height (2) + width (2)
    sof0_payload = b"\x08" + struct.pack(">HH", height, width)
    sof0 = b"\xff\xc0" + struct.pack(">H", 2 + len(sof0_payload)) + sof0_payload
    return soi + app0 + sof0


class TestImageDimensions:
    def test_nonexistent_file_returns_none(self):
        assert image_dimensions("/nonexistent/path.png") is None

    def test_png_returns_dimensions(self, tmp_path):
        p = tmp_path / "img.png"
        p.write_bytes(png_bytes(320, 480))
        assert image_dimensions(str(p)) == (320, 480)

    def test_jpeg_returns_dimensions(self, tmp_path):
        p = tmp_path / "img.jpg"
        p.write_bytes(jpeg_bytes(200, 300))
        assert image_dimensions(str(p)) == (200, 300)

    def test_non_image_bytes_returns_none(self, tmp_path):
        p = tmp_path / "data.bin"
        p.write_bytes(b"\x00\x01\x02\x03\x04\x05\x06\x07")
        assert image_dimensions(str(p)) is None

    def test_jpeg_truncated_at_soi_returns_none(self, tmp_path):
        # Only SOI marker, no further bytes — triggers `len(b) < 2` break
        p = tmp_path / "trunc.jpg"
        p.write_bytes(b"\xff\xd8")
        assert image_dimensions(str(p)) is None

    def test_jpeg_with_eoi_marker_returns_none(self, tmp_path):
        # SOI + EOI (D9) — triggers the `marker in (0xD8, 0xD9)` continue branch, then EOF
        p = tmp_path / "eoi.jpg"
        p.write_bytes(b"\xff\xd8\xff\xd9")
        assert image_dimensions(str(p)) is None

    def test_jpeg_truncated_seg_len_returns_none(self, tmp_path):
        # SOI + APP0 marker + only 1 byte for segment length — triggers `len(seg_len) < 2` break
        p = tmp_path / "trunc_seg.jpg"
        p.write_bytes(b"\xff\xd8\xff\xe0\x00")
        assert image_dimensions(str(p)) is None

    def test_png_too_short_returns_none(self, tmp_path):
        # Valid PNG magic but truncated — triggers struct.error
        p = tmp_path / "short.png"
        p.write_bytes(b"\x89PNG\r\n\x1a\n\x00")
        assert image_dimensions(str(p)) is None


class TestSvgPersonInit:
    def test_no_photo_no_text_lines(self):
        svg = SvgPerson(make_person())
        assert svg.width == SvgComponent.MIN_WIDTH
        assert svg.height == SvgComponent.PADDING * 2

    def test_no_photo_with_text_lines(self):
        text_lines = [TextLine(text="MacDonald, Ewan"), TextLine(text="b. 1909")]
        svg = SvgPerson(make_person(text_lines=text_lines))
        assert svg.height == SvgComponent.PADDING * 2 + 2 * SvgComponent.LINE_HEIGHT

    def test_with_valid_photo(self, tmp_path):
        p = tmp_path / "photo.png"
        p.write_bytes(png_bytes(80, 100))
        svg = SvgPerson(make_person(photo=str(p)))
        assert svg.photo_width == 64
        assert svg.height == SvgComponent.PADDING * 2 + SvgComponent.PHOTO_HEIGHT + SvgComponent.PADDING

    def test_with_nonexistent_photo_uses_default_width(self):
        svg = SvgPerson(make_person(photo="/no/such/file.png"))
        assert svg.photo_width == SvgComponent.PHOTO_WIDTH

    def test_long_text_line_widens_component(self):
        long_text = "a" * 100
        svg = SvgPerson(make_person(text_lines=[TextLine(text=long_text)]))
        expected = len(long_text) * SvgComponent.FONT_SIZE * 0.5 + SvgComponent.PADDING * 2
        assert svg.width >= expected

    def test_photo_wider_than_text_widens_component(self, tmp_path):
        p = tmp_path / "wide.png"
        p.write_bytes(png_bytes(400, 100))
        svg = SvgPerson(make_person(photo=str(p), text_lines=[TextLine(text="hi")]))
        assert svg.width >= 400 * 0.8


class TestSvgPersonRender:
    def test_renders_rect(self):
        svg = SvgPerson(make_person(text_lines=[TextLine(text="Smith, John")]))
        result = svg.render()
        assert "<rect" in result

    def test_default_fill_when_no_fillcolor(self):
        svg = SvgPerson(make_person())
        result = svg.render()
        assert 'fill="#ffffff"' in result

    def test_custom_fillcolor(self):
        svg = SvgPerson(make_person(fillcolor="#e0e0ff"))
        result = svg.render()
        assert 'fill="#e0e0ff"' in result

    def test_render_without_photo_no_image_tag(self):
        svg = SvgPerson(make_person(text_lines=[TextLine(text="Smith, John")]))
        result = svg.render()
        assert "<image" not in result

    def test_render_with_photo_has_image_tag(self, tmp_path):
        p = tmp_path / "photo.png"
        p.write_bytes(png_bytes(80, 100))
        svg = SvgPerson(make_person(photo=str(p), text_lines=[TextLine(text="Smith, John")]))
        result = svg.render()
        assert "<image" in result
        assert str(p) in result

    def test_render_text_present(self):
        svg = SvgPerson(make_person(text_lines=[TextLine(text="b. 1909")]))
        result = svg.render()
        assert "b. 1909" in result

    def test_render_without_map_url_no_link(self):
        svg = SvgPerson(make_person(text_lines=[TextLine(text="b. 1909", map_url=None)]))
        result = svg.render()
        assert "<a href=" not in result

    def test_render_with_map_url_has_link(self):
        url = "https://maps.google.com?q=51.5,0.1"
        svg = SvgPerson(make_person(text_lines=[TextLine(text="London", map_url=url)]))
        result = svg.render()
        assert "<a href=" in result
        assert url in result

    def test_render_with_map_url_uses_blue_color(self):
        svg = SvgPerson(make_person(text_lines=[TextLine(text="London", map_url="https://example.com")]))
        result = svg.render()
        assert "#0000EE" in result

    def test_render_without_map_url_uses_black_color(self):
        svg = SvgPerson(make_person(text_lines=[TextLine(text="London")]))
        result = svg.render()
        assert "#000000" in result

    def test_render_escapes_special_chars_in_text(self):
        svg = SvgPerson(make_person(text_lines=[TextLine(text="test & <data>")]))
        result = svg.render()
        assert "&amp;" in result
        assert "&lt;" in result

    def test_render_escapes_photo_path(self, tmp_path):
        p = tmp_path / 'has"quote.png'
        p.write_bytes(png_bytes(80, 100))
        svg = SvgPerson(make_person(photo=str(p)))
        result = svg.render()
        assert "&quot;" in result

    def test_render_with_xy_offset(self):
        svg = SvgPerson(make_person(text_lines=[TextLine(text="b. 1909")]))
        result = svg.render(50, 100)
        assert 'x="50"' in result
        assert 'y="100"' in result
