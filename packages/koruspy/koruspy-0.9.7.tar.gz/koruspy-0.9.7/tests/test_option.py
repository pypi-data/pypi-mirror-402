# tests/test_option.py
from koruspy import Some, nothing, OptionUnwrapError

def test_some_unwrap():
    s = Some(10)
    assert s.finalize() == 10

def test_nothing_behavior():
    n = nothing
    try:
        n.finalize()
        assert False  # não deve chegar aqui
    except OptionUnwrapError as e:
        assert str(e) == "Option doesnt has a value, try using `unwrap_or()` or `unwrap_or_else()` for fallback value"  # ou a mensagem que você usa