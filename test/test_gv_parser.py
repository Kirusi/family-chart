import pytest

from family_chart.graph_settings import GraphSettings
from family_chart.gv_parser import GvParser
from family_chart.person import Person
from family_chart.relationship import Relationship

PEOPLE_FILE = "data/sample_people_only.gv"
FAMILY_FILE = "data/sample_families_only.gv"
REL_FILE = "data/sample_relationships_only.gv"


@pytest.fixture
def parser():
    return GvParser()


class TestParseAttrBlock:
    def test_quoted_values(self, parser):
        result = parser.parse_attr_block('style="solid,filled" fontsize="14"')
        assert result == {"style": "solid,filled", "fontsize": "14"}

    def test_unquoted_values(self, parser):
        result = parser.parse_attr_block("len=0.5 style=solid fontsize=14")
        assert result == {"len": "0.5", "style": "solid", "fontsize": "14"}

    def test_mixed_quoted_unquoted(self, parser):
        result = parser.parse_attr_block('len=0.5 style="solid" fontsize=14')
        assert result == {"len": "0.5", "style": "solid", "fontsize": "14"}

    def test_empty_string(self, parser):
        assert parser.parse_attr_block("") == {}

    def test_single_pair(self, parser):
        assert parser.parse_attr_block('rankdir="TB"') == {"rankdir": "TB"}


class TestParseLabel:
    def test_name_only(self, parser):
        html = "<TABLE><TR><TD>MacDonald, Ewan</TD></TR></TABLE>"
        photo, text_lines = parser.parse_label(html)
        assert text_lines[0].text == "MacDonald, Ewan"
        assert text_lines[0].map_url is None
        assert photo is None
        assert len(text_lines) == 1

    def test_photo_extracted(self, parser):
        html = '<TABLE><TR><TD><IMG SRC="/path/to/photo.png"/></TD></TR><TR><TD>Campbell, Fiona</TD></TR></TABLE>'
        photo, text_lines = parser.parse_label(html)
        assert text_lines[0].text == "Campbell, Fiona"
        assert photo == "/path/to/photo.png"

    def test_birth_text_line_with_map_url(self, parser):
        html = (
            "<TABLE>"
            "<TR><TD>Smith, John</TD></TR>"
            '<TR><TD HREF="https://maps.google.com?q=51.5,0.1" ALIGN="LEFT">'
            "b. 1900 London, UK (51.5 N, 0.1 E)</TD></TR>"
            "</TABLE>"
        )
        photo, text_lines = parser.parse_label(html)
        assert text_lines[0].text == "Smith, John"
        assert text_lines[1].text == "b. 1900 London, UK (51.5 N, 0.1 E)"
        assert text_lines[1].map_url == "https://maps.google.com?q=51.5,0.1"
        assert len(text_lines) == 2

    def test_birth_text_line_without_map_url(self, parser):
        html = '<TABLE><TR><TD>Fraser, Hamish</TD></TR><TR><TD ALIGN="LEFT">b. 1870</TD></TR></TABLE>'
        photo, text_lines = parser.parse_label(html)
        assert text_lines[0].text == "Fraser, Hamish"
        assert text_lines[1].text == "b. 1870"
        assert text_lines[1].map_url is None

    def test_birth_and_death_text_lines(self, parser):
        html = (
            "<TABLE>"
            "<TR><TD>Campbell, Fiona</TD></TR>"
            '<TR><TD HREF="https://maps.google.com?q=46.32,39.40" ALIGN="LEFT">'
            "b. 1909-08-02 Aberfoyle (46.32 N, 39.4 E)</TD></TR>"
            '<TR><TD HREF="https://maps.google.com?q=42.87,74.61" ALIGN="LEFT">'
            "d. 1987-09-07 Plockton (42.87 N, 74.61 E)</TD></TR>"
            "</TABLE>"
        )
        photo, text_lines = parser.parse_label(html)
        assert text_lines[0].text == "Campbell, Fiona"
        assert text_lines[1].text.startswith("b.")
        assert text_lines[2].text.startswith("d.")
        assert len(text_lines) == 3

    def test_spacer_td_ignored(self, parser):
        html = '<TABLE><TR><TD>Jones, Mary</TD></TR><TR><TD CELLPADDING="4"><BR/></TD></TR></TABLE>'
        photo, text_lines = parser.parse_label(html)
        assert text_lines[0].text == "Jones, Mary"
        assert len(text_lines) == 1

    def test_spacer_td_ignored_with_whitespace(self, parser):
        html = '<TABLE><TR><TD>  Jones, Mary\t</TD></TR><TR><TD CELLPADDING="4"><BR/></TD></TR></TABLE>'
        photo, text_lines = parser.parse_label(html)
        assert text_lines[0].text == "Jones, Mary"
        assert len(text_lines) == 1

    def test_empty_html(self, parser):
        photo, text_lines = parser.parse_label("")
        assert photo is None
        assert text_lines == []


class TestParseHeaderLine:
    def test_metadata_stat(self, parser):
        settings = GraphSettings()
        parser.parse_header_line("# Number of people in database: 1159", settings)
        assert settings.metadata["Number of people in database"] == 1159

    def test_people_of_interest(self, parser):
        settings = GraphSettings()
        parser.parse_header_line("# -> I0057, Sean Murphy", settings)
        assert settings.people_of_interest == [("I0057", "Sean Murphy")]

    def test_edge_defaults(self, parser):
        settings = GraphSettings()
        parser.parse_header_line("edge [len=0.5 style=solid fontsize=14];", settings)
        assert settings.edge_defaults == {"len": "0.5", "style": "solid", "fontsize": "14"}

    def test_node_defaults(self, parser):
        settings = GraphSettings()
        parser.parse_header_line("node [style=filled fontsize=14];", settings)
        assert settings.node_defaults == {"style": "filled", "fontsize": "14"}

    def test_graph_attrs(self, parser):
        settings = GraphSettings()
        parser.parse_header_line("graph [fontsize=14];", settings)
        assert settings.graph_attrs == {"fontsize": "14"}

    def test_toplevel_attr_quoted(self, parser):
        settings = GraphSettings()
        parser.parse_header_line('rankdir="TB";', settings)
        assert settings.attrs["rankdir"] == "TB"

    def test_toplevel_attr_unquoted(self, parser):
        settings = GraphSettings()
        parser.parse_header_line("bgcolor=white;", settings)
        assert settings.attrs["bgcolor"] == "white"

    def test_unrecognised_comment_ignored(self, parser):
        settings = GraphSettings()
        parser.parse_header_line("# some other comment", settings)
        assert settings.metadata == {}
        assert settings.people_of_interest == []

    def test_unrecognised_attr_block_ignored(self, parser):
        settings = GraphSettings()
        parser.parse_header_line("ratio [style=filled];", settings)
        assert settings.edge_defaults == {}
        assert settings.node_defaults == {}
        assert settings.graph_attrs == {}


class TestParseNode:
    def test_basic_node(self, parser):
        attrs = (
            'shape="box" fillcolor="#e0e0ff" style="solid,filled" '
            "label=<<TABLE><TR><TD>MacDonald, Ewan</TD></TR></TABLE>>"
        )
        person = parser.parse_person_node("I0057", attrs)
        assert person.id == "I0057"
        assert person.text_lines[0].text == "MacDonald, Ewan"
        assert person.photo is None
        assert len(person.text_lines) == 1

    def test_node_with_birth_and_death(self, parser):
        attrs = (
            'shape="box" fillcolor="#ffe0e0" style="solid,filled" '
            "label=<<TABLE>"
            "<TR><TD>Campbell, Fiona</TD></TR>"
            '<TR><TD HREF="https://maps.google.com?q=46.32,39.40" ALIGN="LEFT">b. 1909-08-02 Aberfoyle</TD></TR>'
            '<TR><TD HREF="https://maps.google.com?q=42.87,74.61" ALIGN="LEFT">d. 1987-09-07 Plockton</TD></TR>'
            "</TABLE>>"
        )
        person = parser.parse_person_node("I0004", attrs)
        assert person.id == "I0004"
        assert person.text_lines[0].text == "Campbell, Fiona"
        assert len(person.text_lines) == 3

    def test_node_with_photo(self, parser):
        attrs = (
            'shape="box" fillcolor="#e0e0ff" style="solid,filled" '
            "label=<<TABLE>"
            '<TR><TD><IMG SRC="/photos/person.png"/></TD></TR>'
            "<TR><TD>Fraser, Hamish</TD></TR>"
            '<TR><TD ALIGN="LEFT">b. 1870</TD></TR>'
            "</TABLE>>"
        )
        person = parser.parse_person_node("I0058", attrs)
        assert person.photo == "/photos/person.png"
        assert person.text_lines[0].text == "Fraser, Hamish"
        assert person.text_lines[1].text == "b. 1870"

    def test_node_fillcolor(self, parser):
        attrs = 'shape="box" fillcolor="#e0e0ff" style="solid,filled" label=<<TABLE><TR><TD>X</TD></TR></TABLE>>'
        assert parser.parse_person_node("I0001", attrs).fillcolor == "#e0e0ff"
        attrs = 'shape="box" fillcolor="#ffe0e0" style="solid,filled" label=<<TABLE><TR><TD>X</TD></TR></TABLE>>'
        assert parser.parse_person_node("I0002", attrs).fillcolor == "#ffe0e0"

    def test_node_no_label(self, parser):
        person = parser.parse_person_node("I9999", 'shape="box"')
        assert person.id == "I9999"
        assert person.fillcolor is None
        assert person.text_lines == []

    def test_all_marriages_multiple_families(self, parser):
        attrs = (
            'shape="box" fillcolor="#ffe0e0" style="solid,filled" '
            'all_marriages="F0021, F0027" '
            "label=<<TABLE><TR><TD>Campbell, Fiona</TD></TR></TABLE>>"
        )
        person = parser.parse_person_node("I0004", attrs)
        assert person.all_marriages == ["F0021", "F0027"]

    def test_all_marriages_single_family(self, parser):
        attrs = (
            'shape="box" fillcolor="#e0e0ff" style="solid,filled" '
            'all_marriages="F0022" '
            "label=<<TABLE><TR><TD>MacDonald, Ewan</TD></TR></TABLE>>"
        )
        person = parser.parse_person_node("I0057", attrs)
        assert person.all_marriages == ["F0022"]

    def test_all_marriages_empty_list(self, parser):
        attrs = (
            'shape="box" fillcolor="#e0e0ff" style="solid,filled" '
            "label=<<TABLE><TR><TD>Macleod, Alasdair</TD></TR></TABLE>>"
        )
        person = parser.parse_person_node("I1163", attrs)
        assert person.all_marriages == []

    def test_all_marriages_no_comment_attribute(self, parser):
        attrs = (
            'shape="box" fillcolor="#e0e0ff" style="solid,filled" '
            "label=<<TABLE><TR><TD>Unknown Person</TD></TR></TABLE>>"
        )
        person = parser.parse_person_node("I9999", attrs)
        assert person.all_marriages == []

    def test_all_marriages_malformed_json(self, parser):
        attrs = (
            'shape="box" fillcolor="#e0e0ff" style="solid,filled" '
            'comment="{not valid json}" '
            "label=<<TABLE><TR><TD>Unknown Person</TD></TR></TABLE>>"
        )
        person = parser.parse_person_node("I9999", attrs)
        assert person.all_marriages == []


class TestParsePeople:
    def test_returns_settings_people_families(self, parser):
        settings, people, families, _ = parser.parse(PEOPLE_FILE)
        assert isinstance(settings, GraphSettings)
        assert isinstance(people, list)
        assert isinstance(families, list)
        assert all(isinstance(p, Person) for p in people)

    def test_people_count(self, parser):
        # FIXME: VK: don't check against files
        _, people, _, _ = parser.parse(PEOPLE_FILE)
        assert len(people) == 10

    def test_no_families_in_people_file(self, parser):
        _, _, families, _ = parser.parse(PEOPLE_FILE)
        assert families == []

    def test_metadata_parsed(self, parser):
        settings, _, _, _ = parser.parse(PEOPLE_FILE)
        assert settings.metadata["Number of people in database"] == 1159
        assert settings.metadata["Number of families in database"] == 482

    def test_people_of_interest(self, parser):
        settings, _, _, _ = parser.parse(PEOPLE_FILE)
        assert settings.people_of_interest == [("I0057", "Sean Murphy")]

    def test_graph_attrs_parsed(self, parser):
        settings, _, _, _ = parser.parse(PEOPLE_FILE)
        assert settings.attrs["rankdir"] == "TB"
        assert settings.attrs["bgcolor"] == "white"

    def test_known_person_fields(self, parser):
        _, people, _, _ = parser.parse(PEOPLE_FILE)
        fiona = next(p for p in people if p.id == "I0004")
        assert fiona.text_lines[0].text == "Campbell, Fiona"
        assert fiona.photo is not None
        assert len(fiona.text_lines) == 3
        assert fiona.text_lines[1].text.startswith("b.")
        assert fiona.text_lines[1].map_url is not None
        assert fiona.text_lines[2].text.startswith("d.")

    def test_person_name_only(self, parser):
        _, people, _, _ = parser.parse(PEOPLE_FILE)
        ewan = next(p for p in people if p.id == "I0057")
        assert ewan.text_lines[0].text == "MacDonald, Ewan"
        assert len(ewan.text_lines) == 1

    def test_birth_without_map_url(self, parser):
        _, people, _, _ = parser.parse(PEOPLE_FILE)
        hamish = next(p for p in people if p.id == "I0058")
        birth = next(e for e in hamish.text_lines if e.text.startswith("b."))
        assert birth.map_url is None

    def test_all_marriages_from_file_multiple(self, parser):
        _, people, _, _ = parser.parse(PEOPLE_FILE)
        fiona = next(p for p in people if p.id == "I0004")
        assert fiona.all_marriages == ["F0021", "F0027"]

    def test_all_marriages_from_file_single(self, parser):
        _, people, _, _ = parser.parse(PEOPLE_FILE)
        ewan = next(p for p in people if p.id == "I0057")
        assert ewan.all_marriages == ["F0022"]

    def test_all_marriages_from_file_empty(self, parser):
        _, people, _, _ = parser.parse(PEOPLE_FILE)
        alasdair = next(p for p in people if p.id == "I1163")
        assert alasdair.all_marriages == []


class TestParseFamilies:
    def test_family_count(self, parser):
        _, _, families, _ = parser.parse(FAMILY_FILE)
        assert len(families) == 7

    def test_no_people_in_family_file(self, parser):
        _, people, _, _ = parser.parse(FAMILY_FILE)
        assert people == []

    def test_family_ids(self, parser):
        _, _, families, _ = parser.parse(FAMILY_FILE)
        ids = [f.id for f in families]
        assert "F0021" in ids
        assert "F0027" in ids

    def test_family_with_date_place_and_map_url(self, parser):
        _, _, families, _ = parser.parse(FAMILY_FILE)
        f = next(f for f in families if f.id == "F0021")
        assert len(f.text_lines) == 2
        assert f.text_lines[0].text == "approx. around 1926"
        assert f.text_lines[1].text == "Culross, Fife, Scottland, UK (46.32 N, 39.4 E)"
        assert f.text_lines[0].map_url == "https://maps.google.com?q=46.3211,39.3978"
        assert f.text_lines[1].map_url == "https://maps.google.com?q=46.3211,39.3978"

    def test_family_children_only(self, parser):
        _, _, families, _ = parser.parse(FAMILY_FILE)
        f = next(f for f in families if f.id == "F0022")
        assert len(f.text_lines) == 1
        assert f.text_lines[0].text == "1 child"
        assert f.text_lines[0].map_url is None

    def test_family_fillcolor(self, parser):
        _, _, families, _ = parser.parse(FAMILY_FILE)
        assert all(f.fillcolor == "#ffffe0" for f in families)

    def test_family_with_date_place_children(self, parser):
        _, _, families, _ = parser.parse(FAMILY_FILE)
        f = next(f for f in families if f.id == "F0027")
        assert len(f.text_lines) == 3
        assert f.text_lines[0].text == "1934"
        assert "Plockton" in f.text_lines[1].text
        assert f.text_lines[2].text == "3 children"
        assert all(e.map_url == "https://maps.google.com?q=51.7823,70.2505" for e in f.text_lines)


class TestParseRelationships:
    def test_relationship_count(self, parser):
        _, _, _, rels = parser.parse(REL_FILE)
        assert len(rels) == 18

    def test_no_people_or_families(self, parser):
        _, people, families, _ = parser.parse(REL_FILE)
        assert people == []
        assert families == []

    def test_relationship_fields(self, parser):
        _, _, _, rels = parser.parse(REL_FILE)
        r = rels[0]
        assert isinstance(r, Relationship)
        assert r.from_id == "I0070"
        assert r.to_id == "F0418"
        assert r.attrs == {"arrowhead": "normal", "arrowtail": "none", "dir": "both"}

    def test_parent_to_family_has_no_style(self, parser):
        _, _, _, rels = parser.parse(REL_FILE)
        parent_rels = [r for r in rels if r.to_id == "F0418"]
        assert len(parent_rels) == 2
        assert all("style" not in r.attrs for r in parent_rels)

    def test_family_to_child_has_style_solid(self, parser):
        _, _, _, rels = parser.parse(REL_FILE)
        child_rels = [r for r in rels if r.from_id == "F0418"]
        assert len(child_rels) == 2
        assert all(r.attrs.get("style") == "solid" for r in child_rels)

    def test_subgraph_style_line_not_parsed_as_relationship(self, parser):
        _, _, _, rels = parser.parse(REL_FILE)
        ids = {r.from_id for r in rels} | {r.to_id for r in rels}
        assert "style" not in ids
        assert "invis" not in ids
