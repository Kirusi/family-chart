from family_chart.family import Family
from family_chart.svg_component import SvgComponent
from family_chart.svg_family import SvgFamily
from family_chart.text_line import TextLine


def make_family(id="F0001", fillcolor=None, text_lines=None):
    return Family(id=id, fillcolor=fillcolor, text_lines=text_lines or [])


class TestSvgFamilyInit:
    def test_id_property(self):
        svg = SvgFamily(make_family(id="F0042"))
        assert svg.id == "F0042"

    def test_no_text_lines_uses_min_width(self):
        svg = SvgFamily(make_family(text_lines=[]))
        assert svg.width == SvgComponent.MIN_WIDTH

    def test_no_text_lines_height(self):
        svg = SvgFamily(make_family(text_lines=[]))
        assert svg.height == SvgComponent.PADDING * 2

    def test_text_lines_height(self):
        text_lines = [TextLine(text="1930"), TextLine(text="London, UK")]
        svg = SvgFamily(make_family(text_lines=text_lines))
        assert svg.height == SvgComponent.PADDING * 2 + 2 * SvgComponent.LINE_HEIGHT

    def test_long_text_line_widens_component(self):
        long_text = "a" * 100
        svg = SvgFamily(make_family(text_lines=[TextLine(text=long_text)]))
        expected = long_text.__len__() * SvgComponent.FONT_SIZE * 0.5 + SvgComponent.PADDING * 2
        assert svg.width >= expected

    def test_short_text_line_uses_min_width(self):
        svg = SvgFamily(make_family(text_lines=[TextLine(text="hi")]))
        assert svg.width == SvgComponent.MIN_WIDTH


class TestSvgFamilyRender:
    def test_renders_ellipse(self):
        svg = SvgFamily(make_family(text_lines=[TextLine(text="1930")]))
        result = svg.render()
        assert "<ellipse" in result

    def test_default_fill_when_no_fillcolor(self):
        svg = SvgFamily(make_family(fillcolor=None, text_lines=[]))
        result = svg.render()
        assert 'fill="#ffffff"' in result

    def test_custom_fillcolor(self):
        svg = SvgFamily(make_family(fillcolor="#ffffe0", text_lines=[]))
        result = svg.render()
        assert 'fill="#ffffe0"' in result

    def test_render_text_present(self):
        svg = SvgFamily(make_family(text_lines=[TextLine(text="approx. 1926")]))
        result = svg.render()
        assert "approx. 1926" in result

    def test_render_without_map_url_no_link(self):
        svg = SvgFamily(make_family(text_lines=[TextLine(text="1930", map_url=None)]))
        result = svg.render()
        assert "<a href=" not in result

    def test_render_with_map_url_has_link(self):
        url = "https://maps.google.com?q=51.5,0.1"
        svg = SvgFamily(make_family(text_lines=[TextLine(text="London", map_url=url)]))
        result = svg.render()
        assert "<a href=" in result
        assert url in result

    def test_render_escapes_special_chars_in_text(self):
        svg = SvgFamily(make_family(text_lines=[TextLine(text="test & <data>")]))
        result = svg.render()
        assert "&amp;" in result
        assert "&lt;" in result

    def test_render_escapes_special_chars_in_map_url(self):
        url = 'https://maps.example.com?q=1&z=2"'
        svg = SvgFamily(make_family(text_lines=[TextLine(text="Place", map_url=url)]))
        result = svg.render()
        assert "&amp;" in result
        assert "&quot;" in result

    def test_render_xy_offset_in_ellipse(self):
        svg = SvgFamily(make_family(text_lines=[TextLine(text="1930")]))
        result = svg.render(100, 200)
        assert "cx=" in result
        assert "cy=" in result

    def test_render_multiple_text_lines(self):
        text_lines = [TextLine(text="1934"), TextLine(text="Plockton, UK")]
        svg = SvgFamily(make_family(text_lines=text_lines))
        result = svg.render()
        assert "1934" in result
        assert "Plockton, UK" in result
