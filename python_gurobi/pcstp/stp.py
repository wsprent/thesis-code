import networkx as nx


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


def load_stp(path):
    '''
    Loads an .stp file into a networkX graph
    '''
    g = nx.Graph()
    int_only = True
    with open(path) as f:
        for line in f:
            if line.startswith('SECTION'):
                suffix = line[8:].strip()

                if suffix == 'Graph':
                    int_only = grow_graph(f, g)
                elif suffix == 'Terminals':
                    N, int_only_N = add_terminal_prizes(f, g)
                else:
                    chomp_section(f)
    return g, N, (int_only and int_only_N)
