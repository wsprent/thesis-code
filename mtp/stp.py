import networkx as nx
from mtp import d, BIG_FLOAT

INF = float('inf')


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def chomp_section(f):
    for line in f:
        if line.startswith('END'):
            return


def grow_graph(f, g):
    int_only = True
    for line in f:
        if line.startswith('Nodes'):
            _, num_nodes = line.strip().split()
            num_nodes = int(num_nodes)
            for i in range(1, num_nodes + 1):
                g.add_node(i, prize=0, _prize=0)
            continue
        if line.startswith('Edges'):
            continue
        if line.startswith('END'):
            break

        _, v, u, w = line.strip().split()
        u = int(u)
        v = int(v)
        if is_int(w):
            w = int(w)
        else:
            w = float(w)
            int_only = False

        g.add_edge(u, v, weight=w, _weight=w)
    return int_only


def add_terminal_prizes(f, g):
    N = set()
    int_only = True
    for line in f:
        if line.startswith('Terminals'):
            continue
        if line == 'END\n':
            break
        _, v, p = line.strip().split()
        v = int(v)
        if is_int(p):
            p = int(p)
        else:
            p = float(p)
            int_only = False
        N.add(v)
        g.node[v]['prize'] = g.node[v]['_prize'] = p

    return N, int_only


def add_assignment_costs(f, g):
    int_only = True

    for line in f:
        if line.startswith('AssignmentCosts'):
            continue
        if line == 'END\n':
            break
        _, u, v, c = line.strip().split()
        u = int(u)
        v = int(v)
        if is_int(c):
            c = int(c)
        else:
            c = float(c)
            int_only = False

        if "assignment_costs" not in g.node[u]:
            g.node[u]["assignment_costs"] = {}
        g.node[u]["assignment_costs"][v] = c

    return int_only


def load_pcstp(fp):
    '''
    Loads an .stp file into a networkX graph
    '''
    g = nx.Graph()
    int_only = True
    for line in fp:
        if line.startswith('SECTION'):
            suffix = line[8:].strip()

            if suffix == 'Graph':
                int_only = grow_graph(fp, g)
            elif suffix == 'Terminals':
                N, int_only_N = add_terminal_prizes(fp, g)
            else:
                chomp_section(fp)
    return g, N, (int_only and int_only_N)


def load_mtp(fp):
    '''
    Loads an .stp file in MTP format into a networkX graph
    '''
    g = nx.Graph()
    int_only = True
    for line in fp:
        if line.startswith('SECTION'):
            suffix = line[8:].strip()
            if suffix == 'Graph':
                int_only = grow_graph(fp, g) and int_only
            elif suffix == 'AssignmentCosts':
                int_only = add_assignment_costs(fp, g) and int_only
            else:
                chomp_section(fp)
    return g, int_only
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
        for v in g.nodes:
            if d(g, u, v) < BIG_FLOAT:
                print("D", u, v, d(g, u, v))
    print("END")


def write_stp(g):
    write_header()
    write_graph(g)
    write_assignment_costs(g)
