# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python tool for processing and visualizing family tree data exported from [GRAMPS](https://gramps-project.org/) genealogy software. Input data is Graphviz DOT (`.gv`) files exported by GRAMPS.

## Commands

This project uses [uv](https://docs.astral.sh/uv/) for package management.

```bash
uv run main.py          # run the project
uv add <package>        # add a dependency
uv sync                 # install dependencies
```

## Data Format

`data/` contains Graphviz DOT files from GRAMPS exports (`digraph GRAMPS_graph { ... }`). Each person is a node like `"I0057"` with an HTML label encoding their name, photo, and life events. Families are represented as edges.

## Parser (`family_chart/gv_parser.py`)

```python
from family_chart.gv_parser import GvParser
settings, people = GvParser().parse("data/sample_people.gv")
```

**`GraphSettings`** holds the DOT file's graph-level configuration:
- `attrs` — top-level key/value pairs (`bgcolor`, `rankdir`, etc.)
- `graph_attrs`, `edge_defaults`, `node_defaults` — attribute blocks
- `metadata` — comment lines of the form `# Key: N` (people/family counts)
- `people_of_interest` — `[(id, name)]` from `# -> ID, Name` comments

**`Person`** fields:
- `id` — node ID string, e.g. `"I0057"`
- `name` — full name string, e.g. `"MacDonald, Ewan"` (`None` if absent)
- `photo` — path from the `<IMG SRC="...">` tag, or `None`
- `entries` — `list[Entry]` of life event strings (birth, death, etc.)

**`Entry`** fields:
- `text` — raw label string, e.g. `"b. 1909-08-02 Aberfoyle, Stirling, UK (46.32 N, 39.4 E)"`
- `map_url` — Google Maps URL from the TD's `HREF`, or `None` if no location data

Event cells are identified by `ALIGN="LEFT"` on their `<TD>`; name cells have no alignment attribute.
