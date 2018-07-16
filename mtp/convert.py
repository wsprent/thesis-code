#! /usr/bin/env python3

import networkx as nx
import gurobipy as grb
import numpy as np

import random
import sys

import argparse
import itertools

from stp import load_pcstp, write_stp
from mtp import d, pairwise

DESCRIPTION = """
 Converts an STP PCSTP instance to a MTP instance using various methods:
 --
"""
INF = float('inf')


def connect_graph(g):
    source_nodes = set()
    for i, j in pairwise(nx.connected_components(g)):
        source_nodes |= i

        u = random.choice(tuple(source_nodes))
        v = random.choice(tuple(j))

        cost = sum(g[u][k]['weight'] for k in g.adj[u]) * 1.0 / len(g.adj[u])
        g.add_edge(u, v, weight=cost)
    return g


def assignment_by_distance(g, be_int=True):
    """
    Assigns prizes as:
    prize * (d_ij / avg_dist)
    """
    shortest = dict(nx.algorithms.all_pairs_dijkstra_path_length(g))
    avg_p = sum(g.node[v]["prize"] for v in g.nodes) / g.number_of_nodes()
    for v in g.nodes:
        d = {}
        p = g.node[v]["prize"] or avg_p
        dists = shortest[v]
        avg_dist = sum(dists.values()) * 1.0 / len(dists.values())

        for u in g.nodes:
            dist = dists[u] if u in dists else INF
            if p > 0:
                dist = p * (dist / avg_dist) if avg_dist else INF
                d[u] = int(dist) if be_int else dist
            else:
                d[u] = 0
        g.node[v]["assignment_costs"] = d

    return g


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument("-f", help="The PCSTP instance as a stp file")

    args = parser.parse_args()

    if args.f:
        with open(args.f) as fp:
            g, N, int_only = load_pcstp(fp)
    else:
        g, N, int_only = load_pcstp(sys.stdin)
    connect_graph(g)
    assignment_by_distance(g)

    write_stp(g)


if __name__ == "__main__":
    main()
