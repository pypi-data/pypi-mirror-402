import pytest
from koruspy import Okay, Err


def test_okay_basic():
    r = Okay(10)

    assert r.is_okay() is True
    assert r.is_err() is False
    assert r.unwrap() == 10


def test_err_basic():
    err = ValueError("falhou")
    r = Err(err)

    assert r.is_okay() is False
    assert r.is_err() is True
    assert r.unwrap_err() is err


def test_unwrap_err_raises_on_okay():
    r = Okay(5)

    with pytest.raises(Exception):
        r.unwrap_err()


def test_unwrap_raises_on_err():
    r = Err(RuntimeError("boom"))

    with pytest.raises(Exception):
        r.unwrap()


def test_map_on_okay():
    r = Okay(3).map(lambda x: x * 2)

    assert r.is_okay()
    assert r.unwrap() == 6


def test_map_does_not_touch_err():
    err = Exception("x")
    r = Err(err).map(lambda _: 123)

    assert r.is_err()
    assert r.unwrap_err() is err


def test_map_err_on_err():
    r = Err("erro").map_err(lambda e: f"erro: {e}")

    assert r.is_err()