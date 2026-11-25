import pytest
from kir.compile import compile_text

H = "---\nkg: v0.4\n---\n"   # body line i -> file line i+3


def lines(body):
    return [l.strip() for l in compile_text(H + body, "t.kg.md").splitlines()]


def test_named_statement():
    out = lines("@add q = s r o\n")
    for l in ("@add q k.subject s", "@add q k.link r", "@add q k.object o"):
        assert l in out


def test_named_statement_string_object():
    out = lines('@add q = newton name "Isaac Newton"\n')
    assert '@add q k.object "Isaac Newton"' in out


def test_print_name():
    assert "@add k.terminal k.print q" in lines("@print(q)\n")


def test_print_triple_generates_gen():
    out = lines("@print(s r o)\n@print(a b c)\n")
    for l in ("@add gen.1 k.subject s", "@add gen.1 k.link r", "@add gen.1 k.object o",
              "@add k.terminal k.print gen.1", "@add gen.2 k.subject a",
              "@add k.terminal k.print gen.2"):
        assert l in out


def test_world_closed():
    assert "@add k.file set.member k.ClosedWorld" in lines("@world closed\n")


def test_world_open():
    assert "@add k.file set.member k.OpenWorld" in lines("@world open\n")


def test_kir_is_fixed_point():
    src = H + "Some prose.\n@add a b c\n@add q k.subject a  // c\n```\n@print(x)\n```\n"
    assert compile_text(src, "t.kg.md") == src


def test_prose_kept():
    out = compile_text(H + "Hello world.\n@print(q)\n", "t.kg.md")
    assert "Hello world." in out


def _e2(body):
    try:
        return compile_text(H + body, "t.kg.md")
    except Exception as e:  # noqa: BLE001 - error may be raised or returned
        return str(e)


@pytest.mark.parametrize("bad", ["@world maybe\n", "@add q = s r\n", "@print(a b)\n"])
def test_bad_sugar_e2_with_line(bad):
    assert ":5: E2" in _e2("ok\n" + bad)
