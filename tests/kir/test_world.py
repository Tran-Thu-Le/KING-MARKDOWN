import pathlib
import pytest
from kir.world import run_text

H = "---\nkg: v0.4\n---\n"   # body line i -> file line i+3
DATA = ("@add Scientist set.subset Person\n@add newton set.member Scientist\n"
        '@add newton name "Isaac Newton"\n@add leibniz set.member Person\n')


USE = "@import set\n"           # appended at the end so body line numbers stay i+3


def run(body, use=True):
    return run_text(H + body + (USE if use else ""), "t.kg.md")


def out(body):
    o, d = run(body)
    assert d == [], d
    return o


def has(diags, code, lines):
    return any(f": {code}:" in d and any(f":{n}: " in d for n in lines) for d in diags)


# 2. open / closed
def test_open_unknown():
    assert out(DATA + '@print(leibniz name "Leibniz")\n') == ['leibniz name "Leibniz": unknown']


def test_closed_false():
    o = out("@world closed\n" + DATA + '@print(leibniz name "Leibniz")\n')
    assert o == ['leibniz name "Leibniz": false']


def test_explicit_open_unknown():
    assert out("@world open\n" + DATA + "@print(a b c)\n") == ["a b c: unknown"]


def test_true_and_number_format():
    assert out("@add a born 1643\n@print(a born 1643)\n") == ["a born 1643: true"]


def test_print_twice():
    assert out("@add a b c\n@print(a b c)\n@print(a b c)\n") == ["a b c: true"] * 2


# 3. lib
def test_member_via_subset_three_levels():
    o = out("@add a set.subset b\n@add b set.subset c\n@add c set.subset d\n"
            "@add x set.member a\n@print(x set.member d)\n")
    assert o == ["x set.member d: true"]


def test_subset_cycle_terminates():
    o = out("@add A set.subset B\n@add B set.subset A\n@add x set.member A\n"
            "@print(x set.member B)\n@print(A set.subset A)\n")
    assert o == ["x set.member B: true", "A set.subset A: true"]


def test_alias_forward():
    o = out("@add is-a set.equal set.member\n@add n is-a P\n@print(n set.member P)\n")
    assert o == ["n set.member P: true"]


def test_alias_backward():
    o = out("@add is-a set.equal set.member\n@add n set.member P\n@print(n is-a P)\n")
    assert o == ["n is-a P: true"]


def test_subset_cycle_with_alias_terminates():
    o = out("@add is-a set.equal set.member\n@add A set.subset B\n@add B set.subset A\n"
            "@add x is-a A\n@print(x is-a B)\n")
    assert o == ["x is-a B: true"]


# 4. and / or
AND = ("@add q1 = var.x a T\n@add q2 = var.x b T\n@add q3 = var.x c T\n"
       "@add r = q2 k.then q3\n@add q1 k.then r\n")


def test_nested_then_is_and_both():
    assert out(AND + "@add n a T\n@add n b T\n@print(n c T)\n") == ["n c T: true"]


def test_nested_then_is_and_one():
    assert out(AND + "@add n a T\n@print(n c T)\n") == ["n c T: unknown"]


def test_two_rules_is_or():
    body = ("@add p1 = var.x a T\n@add p2 = var.x b T\n@add c = var.x c T\n"
            "@add p1 k.then c\n@add p2 k.then c\n@add n b T\n@print(n c T)\n")
    assert out(body) == ["n c T: true"]


# 5. schema
SCHEMA = ("@add w1 = var.x set.member Person\n@add w2 = var.x name var.n\n"
          "@add e = var.x error missing-name\n@add r = w2 k.else e\n@add w1 k.then r\n")


def test_schema():
    o = out(DATA + SCHEMA + "@print(leibniz error missing-name)\n@print(newton error missing-name)\n")
    assert o == ["leibniz error missing-name: true", "newton error missing-name: unknown"]


def test_schema_name_added():
    o = out(DATA + '@add leibniz name "Leibniz"\n' + SCHEMA + "@print(leibniz error missing-name)\n")
    assert o == ["leibniz error missing-name: unknown"]


def test_lib_with_else_no_e12():
    _, d = run(DATA + SCHEMA)
    assert not any("E12" in x for x in d)


def test_print_subrule_triple():
    assert out(SCHEMA + "@print(r)\n") == ["w2 k.else e: unknown"]


# 6. errors (line = body line + 3)
def test_e16_fact_with_var():
    _, d = run("@add a b c\n@add a b var.x\n")
    assert has(d, "E16", [5])


def test_e15_missing_object():
    _, d = run("@add q k.subject a\n@add q k.link b\n@print(q)\n")
    assert has(d, "E15", [4, 5, 6])


def test_e15_duplicate_subject():
    _, d = run("@add q = a b c\n@add q k.subject z\n")
    assert has(d, "E15", [4, 5])


def test_e14_print_non_statement():
    _, d = run("@add a b c\n@print(foo)\n")
    assert has(d, "E14", [5])


def test_e14_print_pattern():
    _, d = run("@print(var.x b c)\n")
    assert has(d, "E14", [4])


def test_e14_then_to_non_statement():
    _, d = run("@add q = var.x a b\n@add q k.then foo\n")
    assert has(d, "E14", [5])


def test_e14_conclusion_k_link():
    _, d = run("@add q = var.x a b\n@add c = var.x k.print b\n@add q k.then c\n")
    assert has(d, "E14", [5, 6])


def test_e14_conclusion_set_equal():
    _, d = run("@add q = var.x a var.y\n@add c = var.x set.equal var.y\n@add q k.then c\n")
    assert has(d, "E14", [5, 6])


def test_e13_both_worlds():
    _, d = run("@world closed\n@world open\n")
    assert has(d, "E13", [4, 5])


def test_e12_negative_cycle():
    body = ("@add c = var.x m T\n@add pa = var.x a T\n@add pb = var.x b T\n"
            "@add r1 = pa k.else pb\n@add c k.then r1\n"
            "@add r2 = pb k.else pa\n@add c k.then r2\n")
    _, d = run(body)
    assert has(d, "E12", range(4, 11))


def test_e11_unsafe_var():
    _, d = run("@add c = var.x a b\n@add e = var.y d b\n@add c k.then e\n")
    assert has(d, "E11", [6])


def test_e11_unsafe_negated_shared_var():
    _, d = run("@add c = var.x a b\n@add n = var.y d b\n@add e = var.y f b\n"
               "@add r = n k.else e\n@add c k.then r\n")
    assert has(d, "E11", [8])


def test_alias_to_k_print_no_double_print():
    assert out("@add foo set.equal k.print\n@print(a b c)\n") == ["a b c: unknown"]


# 7. named statement does not assert its triple
def test_named_statement_not_asserted():
    assert out("@add q = a b c\n@print(q)\n") == ["a b c: unknown"]


# 8. literal-subject conclusion skipped; @addx is prose
def test_literal_subject_conclusion_skipped():
    body = ('@add n name "Isaac"\n@add q1 = var.x name var.v\n@add q2 = var.v tag yes\n'
            '@add q1 k.then q2\n@print(n name "Isaac")\n')
    assert out(body) == ['n name "Isaac": true']


def test_addx_is_prose():
    assert out("@addx a b c\n@print(a b c)\n") == ["a b c: unknown"]


# 9. examples
EX = sorted((pathlib.Path(__file__).parents[2] / "examples" / "kir").glob("world-*.kg.md")) + sorted((pathlib.Path(__file__).parents[2] / "examples" / "kir").glob("logic-*.kg.md"))


@pytest.mark.skipif(not EX, reason="no world examples")
@pytest.mark.parametrize("p", EX or [None], ids=lambda p: getattr(p, "name", "none"))
def test_examples(p):
    o, d = run_text(p.read_text(encoding="utf-8"), p.name)
    exp = p.with_name(p.name.replace(".kg.md", ".expected.txt")).read_text(encoding="utf-8")
    assert d == [] and o == [l for l in exp.splitlines() if l.strip()]
