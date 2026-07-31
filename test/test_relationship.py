from family_chart.relationship import Relationship


class TestConstructor:
    def test_default_constructor(self):
        rel = Relationship("I1", "F1")
        assert rel.from_id == "I1"
        assert rel.to_id == "F1"
        assert rel.attrs is None
        assert rel.source == ""
        assert rel.lookup_key == "I1_F1"

    def test_all_arguments(self):
        attrs = {"style": "solid"}
        rel = Relationship("F1", "I2", attrs=attrs, source='"F1" -> "I2" [ style=solid ];')
        assert rel.from_id == "F1"
        assert rel.to_id == "I2"
        assert rel.attrs == attrs
        assert rel.source == '"F1" -> "I2" [ style=solid ];'
        assert rel.lookup_key == "F1_I2"


class TestClone:
    def test_returns_equal_independent_copy(self):
        rel = Relationship("I1", "F1", attrs={"style": "solid"}, source='"I1" -> "F1" [ style=solid ];')
        cloned = rel.clone()
        assert cloned is not rel
        assert cloned.from_id == rel.from_id
        assert cloned.to_id == rel.to_id
        assert cloned.attrs == rel.attrs
        assert cloned.source == rel.source
        assert cloned.lookup_key == rel.lookup_key

    def test_attrs_are_deep_copied(self):
        rel = Relationship("I1", "F1", attrs={"style": "solid"})
        cloned = rel.clone()
        cloned.attrs["style"] = "dotted"
        assert rel.attrs == {"style": "solid"}

    def test_clone_with_none_attrs(self):
        rel = Relationship("I1", "F1")
        cloned = rel.clone()
        assert cloned.attrs is None


class TestRender:
    def test_no_attrs(self):
        rel = Relationship("I1", "F1")
        assert rel.render() == '"I1" -> "F1";'

    def test_empty_attrs(self):
        rel = Relationship("I1", "F1", attrs={})
        assert rel.render() == '"I1" -> "F1";'

    def test_single_attr(self):
        rel = Relationship("F1", "I2", attrs={"style": "solid"})
        assert rel.render() == '"F1" -> "I2" [ style=solid ];'

    def test_multiple_attrs_in_order(self):
        rel = Relationship("I1", "F1", attrs={"arrowhead": "normal", "arrowtail": "none", "dir": "both"})
        assert rel.render() == '"I1" -> "F1" [ arrowhead=normal arrowtail=none dir=both ];'
