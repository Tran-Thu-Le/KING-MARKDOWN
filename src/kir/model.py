"""Mô hình đồ thị KING IR: node, cạnh (key = link), id phát biểu tùy chọn."""
from dataclasses import dataclass, field

BUILTIN_NODES = ("node", "link", "type", "value", "is-a")
DEFAULT_LANGUAGES = ("markdown", "latex", "typst", "python", "cpp", "json")
RESERVED = {"node", "link", "type", "value", "is-a", "lang", "body", "=", "number",
            "string", "boolean", "true", "false", "none", "language"}


@dataclass
class Diag:
    code: str          # E1..E6 hoặc W
    file: str
    line: int
    msg: str

    def __str__(self):
        return f"{self.file}:{self.line}: {self.code}: {self.msg}"


@dataclass
class Graph:
    stem: str
    nodes: dict = field(default_factory=dict)   # id -> attrs
    edges: list = field(default_factory=list)   # (src, dst, key, attrs)
    derived: list = field(default_factory=list)  # phát biểu có ?x (chỉ lưu)

    def add_node(self, nid, **attrs):
        self.nodes.setdefault(nid, {}).update(attrs)
        return nid

    def add_edge(self, s, o, key, sid=None, line=None):
        attrs = {}
        if sid:
            attrs["id"] = sid
        self.edges.append((s, o, key, attrs))

    def to_dict(self):
        """node-link JSON (khớp nx.node_link_data(G, edges="links"))."""
        return {
            "directed": True, "multigraph": True,
            "graph": {"kg": "v0.4", "stem": self.stem, "derived": self.derived},
            "nodes": [{**a, "id": n} for n, a in self.nodes.items()],
            # thứ tự cạnh theo node nguồn (như networkx) để round-trip giống hệt
            "links": [{**a, "source": s, "target": o, "key": k}
                      for n in self.nodes for s, o, k, a in self.edges if s == n],
        }
