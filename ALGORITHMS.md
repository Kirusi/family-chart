> is there the best algorithm to render a genealogical tree?

There's no single "best" algorithm — it depends on which view you're rendering:

For pedigree (ancestor) charts

Reingold-Tilford (or Walker's O(n) variant) is the standard. It treats the tree as a strict binary tree (person → 2 parents), produces compact, aesthetically pleasing layouts, and handles wide trees well.

For descendant charts with marriages

Sugiyama framework (what Graphviz's dot uses internally) is the go-to. It handles the DAG structure (a person appearing as child in one family and parent in another) by:
1. Assigning nodes to layers (generations)
2. Minimizing edge crossings (NP-hard, so heuristics like barycenter/median are used)
3. Assigning x-coordinates within layers

The hard problem: pedigree collapse

When cousins marry or ancestors appear multiple times, both algorithms break down. Real genealogy software (Gramps included) handles this with heuristics — duplicating nodes or using a hybrid approach.

Practical recommendation for this project

Since you're already consuming Graphviz DOT from Gramps, just use Graphviz's dot layout engine — it implements Sugiyama and is well-tuned for hierarchical graphs. The main knobs are rankdir, ranksep, and nodesep.

If you need custom rendering (e.g., SVG with photos, interactive), ELK (Eclipse Layout Kernel) has a layered algorithm that's more controllable than Graphviz and has JS/Python bindings.