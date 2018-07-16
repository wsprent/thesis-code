#! /usr/bin/env python3

import networkx as nx
import gurobipy as grb
import numpy as np

import argparse
import itertools
import time
import os

from random import random

import mtp

from stp import load_mtp
from mtp import d, pairwise

DESCRIPTION = """
 Solves an instance of the MTP using Gurobi Python.
"""

BIG_INT = np.iinfo(np.int64).max
BIG_FLOAT = np.finfo(np.float64).max
EPSILON = 10**(-5)
MAX_CUTS = 250


def edge(x, i, j):
    return x[i, j] if i <= j else x[j, i]


def build_ilp_model(g):
    model = grb.Model('mtp')

    # Edge Selection
    x = model.addVars(g.edges, vtype=grb.GRB.BINARY)
    # Vertex Assignment
    y = model.addVars(((i, j)
                      for i in g.nodes
                      for j in g.nodes), vtype=grb.GRB.BINARY)

    # OBJECTIVE
    edge_costs = grb.quicksum(g[i][j]['weight'] * x[i, j] for i, j in g.edges)
    assignment_cost = grb.quicksum(d(g, u, v) * y[u, v]
                                   for u in g.nodes
                                   for v in g.nodes)
    model.setObjective(edge_costs + assignment_cost)

    # one less edges than vertices
    model.addConstr(x.sum() == grb.quicksum(y[i, i] for i in g.nodes) - 1,
                    name='x.sum == y.sum - 1')

    # Add all |S| = 2 GSECS
    for i, j in g.edges:
        model.addConstr(x[i, j] <= y[i, i])
        model.addConstr(x[i, j] <= y[j, j])  # ??

    # All Vertices must be assigned
    for i in g.nodes:
        model.addConstr(y.sum(i, '*') == 1)

    # Only assign to vetrices in the facility
    for i in g.nodes:
        for j in g.nodes:
            model.addConstr(y[i, j] <= y[j, j])

    # In the facility iff connected
    for i in g.nodes:
        model.addConstr(y[i, i] <=
                        grb.quicksum(edge(x, i, j) for j in g.adj[i]))
        for j in g.adj[i]:
            model.addConstr(y[i, i] >= edge(x, i, j))
    return model, x, y


def sum_edges(S, x):
    lhs = grb.LinExpr()

    for i, j in itertools.combinations(S, 2):
        if (i, j) in x:
            lhs.add(x[i, j])
        elif (j, i) in x:
            lhs.add(x[j, i])
    return lhs


def separate_gsec_rel(model, x, y, x_bar, y_bar, G):
    F = nx.DiGraph()

    F.add_node(-1)  # source
    F.add_node(-2)  # sink
    for v in G.node:
        F.add_node(v)

    for i, j in G.edges:
        capacity = x_bar[i, j] / 2
        F.add_edge(i, j, capacity=capacity)
        F.add_edge(j, i, capacity=capacity)

    total_source_cap = 0
    for i in G.nodes:
        node = F.node[i]

        capacity = 0
        for j in G.adj[i]:
            capacity += F[i][j]['capacity']

        node['capacity'] = capacity
        source_cap = max(capacity - y_bar[i, i], 0)
        F.add_edge(-1, i, capacity=source_cap)
        F.add_edge(i, -2, capacity=max(y_bar[i, i] - capacity, 0))

        total_source_cap += source_cap

    cuts = 0
    # solve max flow problems and collect cuts
    for i in sorted(F.nodes):
        if i < 0:
            continue

        i_capacity = F[-1][i]['capacity']
        F[-1][i]['capacity'] = float('inf')

        cut_val, cut = nx.minimum_cut(F, _s=-1, _t=-2)

        S, T = cut

        constr = -1 * (cut_val - total_source_cap) + y_bar[i, i]

        S.discard(-1)

        if constr - EPSILON > 0:
            lhs = sum_edges(S, x)
            rhs = grb.quicksum(y[v, v] for v in S if v != i)
            model.cbCut(lhs <= rhs)

            rhs_bar = grb.quicksum(y_bar[v, v] for v in S if v != i)
            lhs_bar = sum_edges(S, x_bar)
            if lhs_bar.getValue() <= rhs_bar.getValue():
                # print('not violated: ', lhs_bar.getValue(), '<=', rhs_bar.getValue())
                pass
            else:
                cuts += 1

        else:
            rhs_bar = grb.quicksum(y_bar[v, v] for v in S if v != i).getValue()
            lhs_bar = sum_edges(S, x_bar).getValue()
            if lhs_bar > rhs_bar:
                # print('violated: ', lhs_bar, '>', rhs_bar)
                pass

        F[-1][i]['capacity'] = i_capacity
        F[i][-2]['capacity'] = float('inf')

        if cuts >= MAX_CUTS:
            return cuts
    return cuts


def add_gsecs(model, x, y, cycles):
    for cycle in cycles:
        ysum = grb.quicksum(y[v, v] for v in cycle)

        lhs = sum_edges(cycle, x)

        for k in cycle:
            if lhs <= (ysum - y[k, k]):
                model.cbLazy(lhs <= (ysum - y[k, k]))


def edge_weight(x, i, j):
    if (i, j) not in x:
        return x[j, i]
    if (j, i) not in x:
        return x[i, j]
    return max(x[i, j], x[j, i])


def path_length_by_x(p, x_vals):
    length = 0
    for i, j in pairwise(p):
        length += 1 - edge_weight(x_vals, i, j)
    return length


def heuristics(G, x, y, x_val, y_val, model):
    print("heuristics")

    selected = {}
    limit = 0.7
    while len(selected) < 2:
        selected = {i for i in G.nodes
                    if y_val[i, i] >= limit}
        limit -= 0.1
        if limit < 0:
            return

    #selected = {i for i in G.nodes
    #            if y_val[i, i] > random()}
    sp = dict(nx.shortest_path(G))

    spl = {u: {v: path_length_by_x(p, x_val)
               for v, p in d.items()}
           for u, d in sp.items()}

    # spl = dict(nx.shortest_path_length(G))

    GS = nx.Graph()
    for i in selected:
        for j in selected:
            if i >= j:
                continue
            GS.add_edge(i, j, weight=spl[i][j])

    mst = nx.algorithms.tree.minimum_spanning_tree(GS)

    S = set()
    for i, j in mst.edges:
        S = S.union(sp[i][j])

    GH = G.subgraph(S)

    mst = nx.algorithms.tree.minimum_spanning_tree(GH)

    for i in G.nodes:
        for j in G.nodes:
            model.cbSetSolution(y[i, j], 0)

        other_node = -1
        if i in S:
            model.cbSetSolution(y[i, i], 1)
        else:
            min_cost = None
            other_node = None
            for j in S:
                a_cost = d(G, i, j)
                if min_cost is None:
                    min_cost = a_cost
                    other_node = j
                elif a_cost <= min_cost:
                    other_node = j
                    min_cost = d(G, i, j)
            model.cbSetSolution(y[i, other_node], 1)
    for i, j in G.edges:
        model.cbSetSolution(edge(x, i, j), 1
                            if (i, j) in mst.edges else 0)
    print("Heuristics cost:", mtp.cost(mst, G))
    print("Gurobi cost:", model.cbUseSolution())
    model._mst = mst


def callback(G, x, y, model, where):
    if where == grb.GRB.callback.MIPSOL:
        x_val = model.cbGetSolution(x)
        # y_val = model.cbGetSolution(y)

        g = nx.Graph()

        for i, j in x_val.keys():
            if x_val[i, j] > 0.5:
                g.add_edge(i, j)

        cycles = nx.cycle_basis(g)

        add_gsecs(model, x, y, cycles)

    elif where == grb.GRB.callback.MIPNODE:
        x_val = model.cbGetNodeRel(x)
        y_val = model.cbGetNodeRel(y)

        status = model.cbGet(grb.GRB.Callback.MIPNODE_STATUS)
        nodecount = model.cbGet(grb.GRB.Callback.MIPNODE_NODCNT)
        if status == grb.GRB.OPTIMAL:
            cuts = separate_gsec_rel(model, x, y, x_val, y_val, G)
            if cuts > 0:
                # print("Generated", cuts, "cuts.")
                pass
            # 0
            # return

        if status == grb.GRB.OPTIMAL and model._last_node < nodecount - 40:
            model._last_node = nodecount
            heuristics(G, x, y, x_val, y_val, model)


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("mtp", help="The MTP instance as a stp file")
    parser.add_argument("--time", "-t", help="Output optimisation timings")
    parser.add_argument("--time-limit", "-l", help="Set timelimit for the gurobi optimiser",
                        type=int)
    parser.add_argument("-r", "--repeat", metavar="<n>",
                        help="Repeat the optimisation n times - only makes sense with the -t switch",
                        type=int, default=1)
    args = parser.parse_args()

    runs = []
    with open(args.mtp) as fp:
        g, int_only = load_mtp(fp)

    for i in range(args.repeat):
        if args.time is not None:
            start = time.time()
        model, x, y = build_ilp_model(g)

        model.Params.lazyConstraints = 1
        model.Params.preCrush = 1
        model.Params.heuristics = 0

        if args.time_limit:
            model.Params.timeLimit = args.time_limit

        model._int_only = int_only
        model._last_node = -49
        model.modelSense = grb.GRB.MINIMIZE

        for v in g.nodes:
            y[v, v].setAttr(grb.GRB.Attr.BranchPriority, 2)

        model.optimize(lambda m, w: callback(g, x, y, m, w))

        x_val = model.getAttr("X", x)
        y_val = model.getAttr("X", y)

        g_fin = nx.Graph()

        seen = set()
        for i, j in x_val.keys():
            if x_val[i, j] > 0.5:
                seen.add(i)
                seen.add(j)
                print(i, j, x_val[i, j])
                g_fin.add_edge(i, j)

        for i in g.nodes:
            if y_val[i, i] > 0:
                print(i, y_val[i, i])

        print(model.status)
        if args.time is not None:
            end = time.time()
            runs.append((model.status, end - start, model.objVal))

    if args.time is not None:
        directory = os.path.join(args.time, args.mtp.split("/")[-2])
        filename = args.mtp.split("/")[-1] + "." + str(time.time())

        if os.path.exists(directory):
            os.makedirs(directory)
        with open(os.path.join(directory, filename), "w") as f:
            for st, timing, obj in runs:
                print(st, timing, obj, file=f)

if __name__ == "__main__":
    main()
