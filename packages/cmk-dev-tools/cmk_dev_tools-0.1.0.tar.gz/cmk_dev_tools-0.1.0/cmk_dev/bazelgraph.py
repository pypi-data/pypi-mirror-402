#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "graphviz",
#   "networkx",
#   "numpy",
#   "matplotlib",
#   "PyQt5",
# ]
# ///

import sys
from graphviz import Digraph
import networkx as nx
import matplotlib.pyplot as plt


def collect_graph(source):
    nodes = set()
    edges = set()
    for l in map(str.strip, source):
        if any(l.startswith(e) for e in {"{", "}", "digraph", "node"}):
            continue
        if "label=" in l:
            continue
        if any(
            e in l
            for e in {
                "npm_cmk_shared_typing",
                "npm_cmk_frontend_vue",
                "aspect_rules_js",
                "aspect_rules_ts",
                "@platforms",
                "npm_typescript",
                "aspect_bazel_lib",
                "node_modules/",
            }
        ):
            continue
        assert l.startswith('"') and l.endswith('"'), l
        if (pos := l.find("->")) != -1:
            edges.add((l[1 : pos - 2], l[pos + 4 : -1]))
        else:
            nodes.add(l[1:-1])
    for a, b in edges:
        assert a in nodes, a
        assert b in nodes, b
    print(len(nodes))
    for n in nodes:
        print(n)
    G = nx.DiGraph()

    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    pos = nx.spring_layout(G)  # layout algorithm

    nx.draw(G, pos, with_labels=True, node_size=2000, node_color="lightblue", arrows=True)
    plt.show()


if __name__ == "__main__":
    collect_graph(sys.stdin)
