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


class TestRowLayoutInit:
    def test_initial_state(self):
        row = SvgRowLayout()
        assert row.components == []
        assert row.height == 0
        assert row.width == 0


class TestRowLayoutAddComponent:
    def test_add_component(self):
        row = SvgRowLayout()
        comp = _StubComponent(100, 50)
        row.add_component(comp)
        assert comp in row.components

    def test_add_multiple_components(self):
        row = SvgRowLayout()
        c1, c2 = _StubComponent(100, 50), _StubComponent(80, 40)
        row.add_component(c1)
        row.add_component(c2)
        assert row.components == [c1, c2]


class TestRowLayoutCalculateDimensions:
    def test_single_component_height(self):
        row = SvgRowLayout()
        row.add_component(_StubComponent(100, 50))
        row.calculate_dimensions()
        assert row.height == 50

    def test_single_component_width_includes_padding(self):
        row = SvgRowLayout()
        row.add_component(_StubComponent(100, 50))
        row.calculate_dimensions()
        assert row.width == SvgRowLayout.PADDING * 2 + 100

    def test_multiple_components_height_is_max(self):
        row = SvgRowLayout()
        row.add_component(_StubComponent(100, 50))
        row.add_component(_StubComponent(80, 70))
        row.calculate_dimensions()
        assert row.height == 70

    def test_multiple_components_width_includes_spacers(self):
        row = SvgRowLayout()
        row.add_component(_StubComponent(100, 50))
        row.add_component(_StubComponent(80, 40))
        row.calculate_dimensions()
        expected = SvgRowLayout.PADDING * 2 + 100 + 80 + SvgRowLayout.HSPACER
        assert row.width == expected


class TestRowLayoutRender:
    def test_render_returns_concatenated_output(self):
        row = SvgRowLayout()
        row.add_component(_StubComponent(100, 50, "A"))
        row.add_component(_StubComponent(80, 50, "B"))
        result = row.render()
        assert result == "AB"

    def test_render_default_y_zero(self):
        calls = []

        class TrackingComp(_StubComponent):
            def render(self, x, y):
                calls.append((x, y))
                return ""

        row = SvgRowLayout()
        row.add_component(TrackingComp(100, 50))
        row.render()
        assert calls[0][1] == 0

    def test_render_component_x_positions(self):
        calls = []

        class TrackingComp(_StubComponent):
            def render(self, x, y):
                calls.append((x, y))
                return ""

        row = SvgRowLayout()
        row.add_component(TrackingComp(100, 50))
        row.add_component(TrackingComp(80, 50))
        row.render()
        assert calls[0][0] == SvgRowLayout.PADDING
        assert calls[1][0] == SvgRowLayout.PADDING + 100 + SvgRowLayout.HSPACER

    def test_render_centers_shorter_component_vertically(self):
        calls = []

        class TrackingComp(_StubComponent):
            def render(self, x, y):
                calls.append((x, y))
                return ""

        row = SvgRowLayout()
        row.add_component(TrackingComp(100, 60))
        row.add_component(TrackingComp(80, 40))
        row.render(y=0)
        # Second component (height=40) should be centered within row height (60)
        assert calls[1][1] == (60 - 40) // 2

    def test_render_with_y_offset(self):
        calls = []

        class TrackingComp(_StubComponent):
            def render(self, x, y):
                calls.append((x, y))
                return ""

        row = SvgRowLayout()
        row.add_component(TrackingComp(100, 50))
        row.render(y=100)
        assert calls[0][1] == 100
