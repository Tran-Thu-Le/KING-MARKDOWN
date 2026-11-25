"""Backend networkx: node-link JSON cho MultiDiGraph (key = link, `id` = id phát biểu)."""
import networkx as nx


def to_networkx(graph):
    """model.Graph -> nx.MultiDiGraph."""
    return nx.node_link_graph(graph.to_dict(), edges="links")


def from_json(data):
    return nx.node_link_graph(data, edges="links")


def to_json(G):
    return nx.node_link_data(G, edges="links")
