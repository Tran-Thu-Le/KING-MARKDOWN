"""and / or / not (Boolean in closed world, Kleene in open world) and @import imports."""
import itertools
import pytest
from kir.compile import compile_text
from kir.world import run_text

H = "---\nkg: v0.4\n---\n"
FACT = "@add a r yes\n"            # a r yes -> true ; a r no -> absent
VAL = {"T": "a r yes", "A": "a r no"}  # A = absent: false (closed) / unknown (open)


def out(body, world="open", name="t.kg.md"):
    o, d = run_text(H + f"@world {world}\n" + FACT + body, name)
    assert d == [], d
    return [line.rsplit(": ", 1)[1] for line in o]


KLEENE = {"T": 2, "U": 1, "F": 0}
WORD = {2: "true", 1: "unknown", 0: "false"}


@pytest.mark.parametrize("x,y", itertools.product("TA", repeat=2))
@pytest.mark.parametrize("world", ["open", "closed"])
def test_truth_tables(x, y, world):
    miss = "U" if world == "open" else "F"
    v = {"T": KLEENE["T"], "A": KLEENE[miss]}
    body = (f"@print({VAL[x]} and {VAL[y]})\n@print({VAL[x]} or {VAL[y]})\n"
            f"@print(not {VAL[x]})\n")
    assert out(body, world) == [WORD[min(v[x], v[y])], WORD[max(v[x], v[y])], WORD[2 - v[x]]]


def test_open_not_unknown_is_unknown_and_excluded_middle_is_unknown():
    assert out("@print(not a r no)\n@print(a r no or not a r no)\n") == ["unknown", "unknown"]


def test_closed_excluded_middle_true():
    assert out("@print(a r no or not a r no)\n", "closed") == ["true"]


def test_open_false_and_unknown_needs_a_false_side():
    # no way to state false yet in open world: F and U never arises; T or U = T
    assert out("@print(a r yes or a r no)\n") == ["true"]


def test_precedence_and_parentheses():
    # not > and > or :  T or (A and A) = T ; (T or A) and A = A
    assert out("@print(a r yes or a r no and a r no)\n@print((a r yes or a r no) and a r no)\n",
               "closed") == ["true", "false"]


def test_named_compound_statements_in_pure_kir():
    body = ("@add p k.subject a\n@add p k.link r\n@add p k.object yes\n"
            "@add n k.subject k.not\n@add n k.link k.of\n@add n k.object p\n"
            "@add c k.subject p\n@add c k.link k.and\n@add c k.object n\n"
            "@add k.terminal k.print c\n")
    assert out(body, "closed") == ["false"]


def test_compound_text_format():
    o, d = run_text(H + FACT + "@print(not (a r yes and a r no))\n", "t.kg.md")
    assert o == ["not ((a r yes) and (a r no)): unknown"]


def test_compile_compound_sugar():
    k = compile_text(H + "@print(not a r b)\n")
    assert "@add gen.2 k.subject k.not" in k and "@add gen.2 k.link k.of" in k
    assert "@add gen.2 k.object gen.1" in k and "@add k.terminal k.print gen.2" in k


@pytest.mark.parametrize("bad", ["@print(a r)", "@print(a r b and)", "@print((a r b)", "@print(a r b))"])
def test_compile_bad_expression_e2(bad):
    o, d = run_text(H + bad + "\n", "t.kg.md")
    assert o == [] and any(":4: E2:" in x for x in d)


def test_compound_cannot_be_rule_condition():
    body = ("@add p = a r yes\n@add q = a r no\n@add c = p k.and q\n@add t = a r z\n@add c k.then t\n")
    o, d = run_text(H + body, "t.kg.md")
    assert any(":8: E14:" in x for x in d)


def test_self_referencing_compound_e14():
    o, d = run_text(H + "@add c = c k.and c\n@print(c)\n", "t.kg.md")
    assert any(":5: E14:" in x for x in d)


# ---- imports ----
SET = "@add Scientist set.subset Person\n@add newton set.member Scientist\n@print(newton set.member Person)\n"


def test_set_rules_need_import():
    assert run_text(H + SET, "t.kg.md")[0] == ["newton set.member Person: unknown"]
    assert run_text(H + "@import set\n" + SET, "t.kg.md")[0] == ["newton set.member Person: true"]


def test_import_is_pure_kir():
    assert "@add k.file k.import set" in compile_text(H + "@import set\n")
    assert run_text(H + "@add k.file k.import set\n" + SET, "t.kg.md")[0] == ["newton set.member Person: true"]


def test_import_missing_e17():
    o, d = run_text(H + "@import nope\n", "t.kg.md")
    assert o == [] and any(":4: E17:" in x for x in d)


def test_import_file_schema(tmp_path):
    (tmp_path / "schema.kg.md").write_text(
        H + "@import set\n@world closed\n@add Scientist set.subset Person\n@print(x y z)\n", encoding="utf-8")
    main = tmp_path / "main.kg.md"
    main.write_text(H + '@import "schema.kg.md"\n@add newton set.member Scientist\n'
                    "@print(newton set.member Person)\n@print(newton name x)\n", encoding="utf-8")
    o, d = run_text(main.read_text(encoding="utf-8"), str(main))
    # rules come through the import; the schema's world (closed) and print do not
    assert d == [] and o == ["newton set.member Person: true", "newton name x: unknown"]


def test_import_cycle_loads_once(tmp_path):
    (tmp_path / "a.kg.md").write_text(H + '@import "b.kg.md"\n@add a r 1\n', encoding="utf-8")
    (tmp_path / "b.kg.md").write_text(H + '@import "a.kg.md"\n@add b r 2\n', encoding="utf-8")
    a = tmp_path / "a.kg.md"
    o, d = run_text(a.read_text(encoding="utf-8") + "@print(b r 2)\n", str(a))
    assert d == [] and o == ["b r 2: true"]


def test_use_is_alias_of_import():
    assert "@add k.file k.import set" in compile_text(H + "@use set\n")
