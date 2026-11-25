import json
import pytest
from kir.export import parse, to_networkx_json, to_turtle, to_networkx, KirError

SRC = '''---
kg: v0.4
---
Prose line @add ignored.
@add newton is-a Person
@add newton born 1643   // comment
@add newton name "Isaac Newton"
@add newton is-a Person
```python
@add x y z
```
'''


def test_json_shape_and_set():
    d = to_networkx_json(parse(SRC))
    assert d["links"] == [{"source": "newton", "target": "Person", "key": "is-a"}]
    node = {n["id"]: n for n in d["nodes"]}["newton"]
    assert node["born"] == 1643 and node["name"] == "Isaac Newton"


def test_networkx_roundtrip():
    nx = pytest.importorskip("networkx")
    G = to_networkx(parse(SRC))
    assert G.has_edge("newton", "Person", key="is-a")
    assert json.loads(json.dumps(nx.node_link_data(G, edges="links")))["links"][0]["key"] == "is-a"


def test_turtle():
    ttl = to_turtle(parse(SRC))
    assert '<urn:kir:newton> <urn:kir:name> "Isaac Newton" .' in ttl
    assert "<urn:kir:newton> <urn:kir:born> 1643 ." in ttl
    assert ttl.count("is-a") == 1


@pytest.mark.parametrize("line", ["@add a b", "@add a b c d", '@add "a" b c'])
def test_errors(line):
    with pytest.raises(KirError):
        parse(line)
