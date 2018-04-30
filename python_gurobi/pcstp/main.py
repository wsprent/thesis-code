#! /usr/bin/env python3

import networkx as nx
import gurobipy as grb
import argparse
import itertools

from functools import partial

DESCRIPTION = """
 Solves an instance of the PCSTP using Gurobi Python.
"""


def chomp_section(f):
    for line in f:
        if line.startswith('END'):
            return


def grow_graph(f, g):
    for line in f:
        if line.startswith('Nodes'):
            continue
        if line.startswith('Edges'):
            continue
        if line.startswith('END'):
            return

        _, v, u, w = line.strip().split()
        u = int(u)
        v = int(v)
        w = float(w)

        g.add_edge(u, v, weight=w)
        g.node[v]['prize'] = 0
        g.node[u]['prize'] = 0


def add_terminal_prizes(f, g):
    for line in f:
        if line.startswith('Terminals'):
            continue
        if line == 'END\n':
            return
        _, v, p = line.strip().split()
        v = int(v)
        p = float(p)

        if v not in g.node:
            g.add_node(v, prize=p)
        else:
            g.node[v]['prize'] = p


def load_stp(path):
    '''
    Loads an .stp file into a networkX graph
    '''
    g = nx.Graph()
    with open(path) as f:
        for line in f:
            if line.startswith('SECTION'):
                suffix = line[8:].strip()

                if suffix == 'Graph':
                    grow_graph(f, g)
                elif suffix == 'Terminals':
                    add_terminal_prizes(f, g)
                else:
                    chomp_section(f)
    return g


def build_ilp_model(g):
    model = grb.Model('pcstp')

    x = model.addVars(g.edges, vtype=grb.GRB.BINARY)
    y = model.addVars(g.nodes, vtype=grb.GRB.BINARY)

    # OBJECTIVE
    edge_costs = grb.quicksum(g[i][j]['weight'] * x[i, j] for i, j in g.edges)
    prize_cost = grb.quicksum(g.node[v]['prize'] * (1 - y[v]) for v in g.nodes)
    model.setObjective(edge_costs + prize_cost)

    # one less edges than vertices
    model.addConstr(x.sum() == (y.sum() - 1))

    # Add all |S| = 2 GSECS
    for i, j in g.edges:
        model.addConstr(x[i, j] <= y[i])
        model.addConstr(x[i, j] <= y[j])

    # degree of nonterminals must be at least 2

    for v in g.node:
        if g.node[v]['prize'] > 0:
            continue
        model.addConstr(x.sum(v, '*') + x.sum('*', v) >= 2 * y[v])

    return model, x, y


def callback(g, x, y, model, where):
    if where == grb.GRB.callback.MIPSOL:
        x_val = model.cbGetSolution(x)
        # y_val = model.cbGetSolution(y)

        g = nx.Graph()

        for i, j in x_val.keys():
            if x_val[i, j] > 0.5:
                g.add_edge(i, j)

        cycles = nx.cycle_basis(g)

        for cycle in cycles:
            ysum = grb.quicksum(y[v] for v in cycle)
            lhs = grb.LinExpr()

            for i, j in itertools.combinations(cycle, 2):
                if (i, j) in x:
                    lhs.add(x[i, j])
                elif (j, i) in x:
                    lhs.add(x[j, i])

            for k in cycle:
                model.cbLazy(lhs <= (ysum - y[k]))


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument('pcstp', help='The PCSTP instance as a stp file')

    args = parser.parse_args()

    g = load_stp(args.pcstp)

    model, x, y = build_ilp_model(g)

    model.Params.lazyConstraints = 1

    model.optimize(lambda m, w: callback(g, x, y, m, w))


if __name__ == '__main__':
    main()
