from family_chart.svg_component import SvgComponent


class TestSvgComponent:
    def setup_method(self):
        self.comp = SvgComponent()

    def test_escape_ampersand(self):
        assert self.comp.escape_text("a & b") == "a &amp; b"

    def test_escape_lt(self):
        assert self.comp.escape_text("<tag") == "&lt;tag"

    def test_escape_gt(self):
        assert self.comp.escape_text("a > b") == "a &gt; b"

    def test_escape_quote(self):
        assert self.comp.escape_text('"q"') == "&quot;q&quot;"

    def test_escape_combined(self):
        assert self.comp.escape_text('a & <b> "c"') == "a &amp; &lt;b&gt; &quot;c&quot;"

    def test_no_special_chars(self):
        assert self.comp.escape_text("hello world") == "hello world"
