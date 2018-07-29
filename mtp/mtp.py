"""
Utilities for the MTP problem on a NetworkX Graph
"""
import numpy as np
import networkx as nx
import random

BIG_INT = np.iinfo(np.int64).max
BIG_FLOAT = np.finfo(np.float64).max


def pairwise(it):
    it = iter(it)

    one = next(it)
    two = next(it)

    while True:
        yield one, two
        one = two
        two = next(it)


def d(g, u, v):
    try:
        return g.node[u]['assignment_costs'].get(v, BIG_FLOAT)
    except Exception as e:
        print(u, v)
        raise e


def cost(T, G):
    cost = 0
    assignment(T, G)

    # edge costs
    for _, _, w in T.edges(data="weight"):
        cost += w

    # assignment costs
    for i, (_, c) in G.nodes(data='assigned'):
        cost += c

    return cost


def assignment(T, G):
    for v in G.nodes:
        if v in T.nodes:
            G.node[v]['assigned'] = v, 0
        else:
            other_node = None
            cost = -1
            for u in T.nodes:
                c = d(G, v, u)
                if other_node is None or c < cost:
                    other_node = u
                    cost = c
            G.node[v]['assigned'] = other_node, cost


def getrec(di, x):
    """
    Recursively get x from d until it does not exist
    """

    default = None

    while x in di:
        default = di[x]
        x = default
    return default


def truncate(g, n, m):
    """
    Truncates the instance by contracting/deleting edges
    without disjoining
    the graph, g, to have n nodes and m edges.
    """

    assignment_map = {}

    gp = g

    node_ratio = n / gp.number_of_nodes()
    while n < gp.number_of_nodes():
        v = random.choice([i for i in gp])
        v_adj = random.choice([i for i in gp.adj[v]])

        # contract v_adj into v
        gp = nx.contracted_nodes(gp, v, v_adj, self_loops=False)

        assignment_map[v_adj] = v
        danger = False
        if gp.number_of_edges() > m:
            target = min(len(gp.adj[v]) * 1.0 * node_ratio, 1)

            while not danger and len(gp.adj[v]) > target:
                i, j, data = random.choice(tuple(gp.edges(v, data=True)))
                gp.remove_edge(i, j)

                if not nx.is_connected(gp):
                    gp.add_edge(i, j, **data)
                    danger = True

    # fix assignments
    # first for contracted nodes
    for u in assignment_map:
        v = getrec(assignment_map, u)
        # u has been contracted to v
        # we take the lowest assignment cost unless zero
        new_assignments = {}
        for i in gp.nodes:
            du = d(g, u, i)
            dv = d(g, v, i)

            if du == 0:
                new_assignments[i] = dv
            elif dv == 0:
                new_assignments[i] = du
            else:
                new_assignments[i] = min(dv, du)

        gp.nodes[v]['assignment_costs'] = new_assignments

    # remove all non existant assignments

    for i in gp.nodes:
        gp.node[i]['assignment_costs'] = {k: v for k, v in gp.node[i]['assignment_costs'].items()
                                          if k in gp}

    # relabel nodes to run from 1 to N
    j = 1
    bmap = {}
    for i in gp.nodes:
        # i is now j
        bmap[i] = j
        j += 1
    lmap = {v: k for k, v in bmap.items()}
    gpp = nx.relabel_nodes(gp, bmap)

    for i in gpp.nodes:
        gpp.node[i]['assignment_costs'] = {bmap[k]: v for k, v in gp.node[lmap[i]]['assignment_costs'].items()}
    return gpp
