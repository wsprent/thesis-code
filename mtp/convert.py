#! /usr/bin/env python3

import networkx as nx
import gurobipy as grb
import numpy as np

import random

import argparse
import itertools

from stp import load_pcstp

DESCRIPTION = """
 Converts an STP PCSTP instance to a MTP instance using various methods:
 --
"""
INF = float('inf')


def assignment_by_distance(g, be_int=True):
    """
    Assigns prizes as:
    prize * (d_ij / avg_dist)
    """
    shortest = dict(nx.algorithms.all_pairs_dijkstra_path_length(g))

    for v in g.nodes:
        d = {}
        p = g.node[v]["prize"]
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


# Writing:

def write_header():
    print("33D32945 STP File, STP Format Version 1.0")
    print()


def write_graph(g):

    print("SECTION Graph")
    print("Nodes", g.number_of_nodes())
    print("Edges", g.number_of_edges())
    for u, v, c in g.edges(data="weight"):
            print("E", u, v, c)
    print("END")
    print()


def write_assignment_costs(g):
    print("SECTION AssignmentCosts")
    for u in g.nodes:
        costs = g.node[u]["assignment_costs"]
        for v in g.nodes:
            if costs[v] < INF:
                print("D", u, v, costs[v])
    print("END")


def write_stp(g):
    write_header()
    write_graph(g)
    write_assignment_costs(g)


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument("pcstp", help="The PCSTP instance as a stp file")

    args = parser.parse_args()

    g, N, int_only = load_pcstp(args.pcstp)

    assignment_by_distance(g)

    write_stp(g)


if __name__ == "__main__":
    main()
