import pytest
from koruspy import Okay, Err
from koruspy import ResultUnwrapError, KoruspyError

def test_okay_unwrap():
    res = Okay(42)
    assert res.unwrap() == 42
    assert res.unwrap_or(0) == 42
    assert res.unwrap_or_else(lambda e: -1) == 42
    assert res.is_okay() is True
    assert res.is_err() is False

def test_okay_unwrap_err_raises():
    res = Okay(42)
    with pytest.raises(ResultUnwrapError):
        res.unwrap_err()

def test_err_unwrap_raises():
    res = Err("falhou")
    with pytest.raises(ResultUnwrapError):
        res.unwrap()

def test_err_unwrap_err_returns_error():
    res = Err("falhou")
    assert res.unwrap_err() == "falhou"
    assert res.is_okay() is False
    assert res.is_err() is True

def test_err_unwrap_or_and_unwrap_or_else():
    res = Err("erro")
    assert res.unwrap_or(99) == 99
    assert res.unwrap_or_else(lambda e: f"default for {e}") == "default for erro"

def test_map_on_okay_and_err():
    res_ok = Okay(10).map(lambda x: x * 2)
    assert isinstance(res_ok, Okay)
    assert res_ok.unwrap() == 20

    res_err = Err("erro").map(lambda x: x * 2)
    assert isinstance(res_err, Err)
    assert res_err.unwrap_err() == "erro"

def test_fold_behavior():
    res_ok = Okay(5)
    res_err = Err("falhou")

    assert res_ok.fold(lambda v: v * 2, lambda e: -1) == 10
    assert res_err.fold(lambda v: v * 2, lambda e: -1) == -1

def test_expect_on_err_raises():
    res = Err("erro")
    with pytest.raises(KoruspyError):
        res.expect("mensagem customizada")