#! /usr/bin/env python3

import networkx as nx
import gurobipy as grb
import numpy as np

import argparse
import itertools

from pcst_fast import pcst_fast

from stp import load_stp

DESCRIPTION = """
 Solves an instance of the PCSTP using Gurobi Python.
"""

BIG_INT = np.iinfo(np.int64).max
BIG_FLOAT = np.finfo(np.float64).max
EPSILON = 10**(-9)
MAX_CUTS = 1


def build_ilp_model(g):
    model = grb.Model('pcstp')

    x = model.addVars(g.edges, vtype=grb.GRB.BINARY)
    y = model.addVars(g.nodes, vtype=grb.GRB.BINARY)

    # OBJECTIVE
    edge_costs = grb.quicksum(g[i][j]['weight'] * x[i, j] for i, j in g.edges)
    prize_cost = grb.quicksum(g.node[v]['prize'] * (1 - y[v]) for v in g.nodes)
    model.setObjective(edge_costs + prize_cost)

    # one less edges than vertices
    model.addConstr(x.sum() == (y.sum() - 1), name='x.sum == y.sum - 1')

    # Add all |S| = 2 GSECS
    for i, j in g.edges:
        model.addConstr(x[i, j] <= y[i])
        model.addConstr(x[i, j] <= y[j])

    # degree of nonterminals must be at least 2

    # for v in g.node:
    #     if g.node[v]['prize'] > 0:
    #         continue
    #     model.addConstr(x.sum(v, '*') + x.sum('*', v) >= 2 * y[v])

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
        source_cap = max(capacity - y_bar[i], 0)
        F.add_edge(-1, i, capacity=source_cap)
        F.add_edge(i, -2, capacity=max(y_bar[i] - capacity, 0))

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

        constr = -1 * (cut_val - total_source_cap) + y_bar[i]

        S.discard(-1)

        if constr > 0:
            rhs = grb.quicksum(y[v] for v in S if v != i)
            lhs = sum_edges(S, x)

            model.cbCut(lhs <= rhs)
            cuts += 1

            rhs_bar = grb.quicksum(y_bar[v] for v in S if v != i)
            lhs_bar = sum_edges(S, x_bar)
            if lhs_bar.getValue() <= rhs_bar.getValue():
                print('not violated: ', lhs_bar.getValue(), '<=', rhs_bar.getValue())

        else:
            rhs_bar = grb.quicksum(y_bar[v] for v in S if v != i).getValue()
            lhs_bar = sum_edges(S, x_bar).getValue()
            if lhs_bar > rhs_bar:
                print('violated: ', lhs_bar, '>', rhs_bar)

        F[-1][i]['capacity'] = i_capacity
        F[i][-2]['capacity'] = float('inf')

        if cuts >= MAX_CUTS:
            return cuts
    return cuts


def add_gsecs(model, x, y, cycles):
    for cycle in cycles:
        ysum = grb.quicksum(y[v] for v in cycle)

        lhs = sum_edges(cycle, x)

        for k in cycle:
            model.cbLazy(lhs <= (ysum - y[k]))


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
        nodecount = model.cbGet(grb.GRB.Callback.MIP_NODCNT)
        if status == grb.GRB.OPTIMAL:
            cuts = separate_gsec_rel(model, x, y, x_val, y_val, G)
            # if cuts > 0:
            # 0
            # return
        if status == grb.GRB.OPTIMAL:
            model._last_node = nodecount
            for v in G.node:
                node = G.node[v]

                if y_val[v] > 0.5:
                    node['prize'] = BIG_INT
                else:
                    node['prize'] = node['_prize']

            for i, j in G.edges:
                edge = G[i][j]
                edge['weight'] = BIG_FLOAT if x_val[i, j] < 0.1 else edge['_weight']

            gw_nodes, gw_edges = gw(G)

            for v in G.nodes:
                model.cbSetSolution(y[v], 1 if v in gw_nodes else 0)

            for i, j in G.edges:
                model.cbSetSolution(x[i, j], 1 if (i, j) in gw_edges else 0)


def gw(g):
    _e = [(i-1, j-1) for i, j in g.edges]
    # print(_e, len(g.node))
    edges = np.array(_e,
                     dtype='int64')
    costs = np.array([g[i][j]['weight'] for i, j in g.edges],
                     dtype='float64')
    prizes = np.array([g.node[v]['prize'] for v in sorted(g.node)],
                      dtype='int64')

    gw_nodes, gw_edges = pcst_fast(edges,
                                   prizes,
                                   costs,
                                   -1,
                                   1,
                                   'strong',
                                   0)
    # print(gw_edges)
    return set(v+1 for v in gw_nodes), set((i+1, j+1) for i, j in edges[gw_edges])


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument('pcstp', help='The PCSTP instance as a stp file')

    args = parser.parse_args()

    g, N, int_only = load_stp(args.pcstp)

    model, x, y = build_ilp_model(g)

    # Get GW initial solution
    gw_nodes, gw_edges = gw(g)

    for v in g.nodes:
        y[v].start = 1 if v in gw_nodes else 0
        y[v].setAttr(grb.GRB.Attr.BranchPriority, 2 if v in N else 0)

    for i, j in g.edges:
        x[i, j].start = 1 if (i, j) in gw_edges else 0

    model.Params.lazyConstraints = 1
    model.Params.preCrush = 1
    model.Params.heuristics = 0

    model._int_only = int_only
    model._last_node = 0
    model.modelSense = grb.GRB.MINIMIZE

    model.optimize(lambda m, w: callback(g, x, y, m, w))


if __name__ == '__main__':
    main()
