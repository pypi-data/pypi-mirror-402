# tests/test_koruspy_full.py
import pytest
from koruspy import Some, nothing,Okay, Err, option_of, ResultUnwrapError, OptionUnwrapError, FrozenSomeList

# -------------------------------
# Testes Option
# -------------------------------

def test_to_float_invalid_string():
    n = Some("abc")
    result = n.to_float()
    assert result == nothing # deve retornar nothing em caso de falha

def test_some_unwrap():
    s = Some(10)
    assert s.finalize() == 10

def test_unwrap_or_else_called():
    n = nothing
    fallback_called = False

    def fallback():
        nonlocal fallback_called
        fallback_called = True
        return 42

    assert n.unwrap_or_else(fallback) == 42
    assert fallback_called is True

def test_to_floatSucess():
    n = Some("3.14")
    result = n.to_float()
    assert result.finalize() == 3.14

def test_map_returns_none():
    s = Some(5)
    mapped = s.map(lambda x: None)
    assert mapped == nothing  # se map retornar None, deve virar nothing

def test_to_floatfail():
    n = nothing
    result = n.to_float()
    assert result.get_value() == nothing


def test_nothing_behavior():
    n = nothing
    with pytest.raises(OptionUnwrapError) as exc_info:
        n.finalize()  # ou n.unwrap() dependendo da implementação
    assert str(exc_info.value) == "Option doesnt has a value, try using `unwrap_or()` or `unwrap_or_else()` for fallback value"

def test_some_unwrapOr():
    s = Some(5)
    assert s.unwrap_or(0) == 5

def test_large_list_some_nothing():
    valores = [Some(i) if i % 2 == 0 else nothing for i in range(1000)]
    resultados = [v.map(lambda x: x*2) for v in valores]
    for i, r in enumerate(resultados):
        if i % 2 == 0:
            assert r.finalize() == i*2
        else:
            assert r == nothing

def test_filter_with_exception():
    s = Some(5)
    def func(x):
        raise ValueError("boom")
    with pytest.raises(ValueError, match="boom") as ve:
        s.filter(func)

def test_nothing_unwrapOr():
    n = nothing
    assert n.unwrap_or(99) == 99

def test_option_map_some():
    s = Some(3)
    mapped = s.map(lambda x: x * 2)
    assert mapped.finalize() == 6

def test_option_map_nothing():
    n = nothing
    mapped = n.map(lambda x: x * 2)
    assert mapped == nothing

def test_option_filter_some_true():
    s = Some(10)
    filtered = s.filter(lambda x: x > 5)
    assert filtered.finalize() == 10

def test_option_filter_some_false():
    s = Some(2)
    filtered = s.filter(lambda x: x > 5)
    assert filtered == nothing

# -------------------------------
# Testes Result
# -------------------------------

def test_result_map_exception_propagates():
    ok = Okay(10)

    def func(x):
        raise RuntimeError("fail")

    with pytest.raises(RuntimeError, match="fail"):
        ok.map(func)

def test_okay_unwrap():
    ok = Okay(42)
    assert ok.unwrap() == 42

def test_okay_map():
    ok = Okay(5)
    mapped = ok.map(lambda x: x + 1)
    assert mapped.unwrap() == 6

def test_err_finalize_raises():
    e = Err("erro")
    with pytest.raises(ResultUnwrapError) as exc_info:
        e.unwrap()
    assert str(exc_info.value) == f"tried to access Err: {e.error}"

def test_err_map_returns_err():
    e = Err("erro")
    mapped = e.map(lambda x: x * 2)
    assert isinstance(mapped, Err)
    assert str(mapped.error) == "erro"

# -------------------------------
# Integração Option + generator
# -------------------------------

def test_generator_with_option():
    arquivos = ["a.txt", None, "b.txt"]
    def arquivos_validos(arquivos):
        for arquivo in arquivos:
            op = option_of(arquivo, "arquivo ignorado")
            if op.is_present():
                yield op.finalize()
    resultados = list(arquivos_validos(arquivos))
    assert resultados == ["a.txt","arquivo ignorado", "b.txt"]

def test_frozen_somelist_with_nothing_hashable():
    a = FrozenSomeList([Some(1), nothing])
    b = FrozenSomeList([Some(1), nothing])

    assert a == b
    assert hash(a) == hash(b)

    d = {a: "ok"}
    assert d[b] == "ok"

def test_generator_with_some_map():
    valores = [Some(1), nothing, Some(3)]
    def processa(valores):
        for v in valores:
            yield v.map(lambda x: x*10)
    resultados = list(processa(valores))
    # Only Some values should be mapped, nothing remains nothing
    assert [r.finalize() if r is not nothing else r for r in resultados] == [10, nothing, 30]