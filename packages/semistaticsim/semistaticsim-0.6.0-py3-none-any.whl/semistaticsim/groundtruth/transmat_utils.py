import networkx as nx

def get_scc(mat):
    # Build a directed graph from the transition matrix
    G = nx.from_numpy_array(mat, create_using=nx.DiGraph)

    # Find all strongly connected components
    sccs = list(nx.strongly_connected_components(G))

    # Pick the largest one
    largest_scc = max(sccs, key=len)
    return list(largest_scc)