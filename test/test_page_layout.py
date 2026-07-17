from family_chart.page_layout import PageLayout
from family_chart.svg_component import SvgComponent
from family_chart.svg_row_layout import SvgRowLayout


class _StubComponent(SvgComponent):
    def __init__(self, width, height, render_result=""):
        super().__init__()
        self.width = width
        self.height = height
        self._render_result = render_result

    def render(self, x, y):
        return self._render_result


def make_row(*component_sizes, render_result=""):
    """Build a RowLayout from (width, height) pairs."""
    row = SvgRowLayout()
    for w, h in component_sizes:
        row.add_component(_StubComponent(w, h, render_result))
    return row


class TestPageLayoutInit:
    def test_initial_state(self):
        page = PageLayout()
        assert page.rows == []
        assert page.height == 0
        assert page.width == 0


class TestPageLayoutAddRow:
    def test_add_row(self):
        page = PageLayout()
        row = make_row((100, 50))
        page.add_row(row)
        assert row in page.rows

    def test_add_multiple_rows(self):
        page = PageLayout()
        r1 = make_row((100, 50))
        r2 = make_row((80, 40))
        page.add_row(r1)
        page.add_row(r2)
        assert page.rows == [r1, r2]


class TestPageLayoutCalculateDimensions:
    def test_single_row_height_includes_padding(self):
        page = PageLayout()
        page.add_row(make_row((100, 50)))
        page.calculate_dimensions()
        assert page.height == PageLayout.PADDING * 2 + 50

    def test_single_row_no_vspacer(self):
        page = PageLayout()
        page.add_row(make_row((100, 50)))
        page.calculate_dimensions()
        # Only one row — no VSPACER added
        assert page.height == PageLayout.PADDING * 2 + 50

    def test_multiple_rows_height_includes_vspacer(self):
        page = PageLayout()
        page.add_row(make_row((100, 50)))
        page.add_row(make_row((100, 40)))
        page.calculate_dimensions()
        expected = PageLayout.PADDING * 2 + 50 + 40 + PageLayout.VSPACER
        assert page.height == expected

    def test_width_is_max_row_width(self):
        page = PageLayout()
        page.add_row(make_row((200, 50)))
        page.add_row(make_row((100, 40)))
        page.calculate_dimensions()
        # Row widths include PADDING*2; wider row dominates
        assert page.width > 0
        # The wider row (200px component + 2*PADDING) should set the page width
        wider_row = SvgRowLayout()
        wider_row.add_component(_StubComponent(200, 50))
        wider_row.calculate_dimensions()
        assert page.width == wider_row.width


class TestPageLayoutRender:
    def test_render_returns_row_output(self):
        page = PageLayout()
        page.add_row(make_row((100, 50), render_result="ROW1"))
        result = page.render()
        assert "ROW1" in result

    def test_render_multiple_rows_concatenated(self):
        page = PageLayout()
        page.add_row(make_row((100, 50), render_result="ROW1"))
        page.add_row(make_row((100, 40), render_result="ROW2"))
        result = page.render()
        assert "ROW1" in result
        assert "ROW2" in result

    def test_render_sets_dimensions(self):
        page = PageLayout()
        page.add_row(make_row((100, 50)))
        page.render()
        assert page.height > 0
        assert page.width > 0

    def test_render_y_advances_between_rows(self):
        render_calls = []

        class TrackingRow:
            def __init__(self, height):
                self.height = height
                self.width = 100

            def calculate_dimensions(self):
                pass

            def render(self, y):
                render_calls.append(y)
                return ""

        page = PageLayout()
        page.add_row(TrackingRow(50))
        page.add_row(TrackingRow(40))
        page.render()
        assert render_calls[0] == PageLayout.PADDING
        assert render_calls[1] == PageLayout.PADDING + 50 + PageLayout.VSPACER
