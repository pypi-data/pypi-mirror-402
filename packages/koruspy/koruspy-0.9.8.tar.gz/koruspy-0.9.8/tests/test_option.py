import pytest
from koruspy import Some, nothing

def test_some_unwrap():
    assert Some(5).unwrap() == 5

def test_nothing_unwrap_raises():
    with pytest.raises(Exception):
        nothing.unwrap()

def test_map():
    assert Some(2).map(lambda x: x * 2).unwrap() == 4
    assert nothing.map(lambda x: x * 2) is nothing

def test_and_then():
    assert Some(2).and_then(lambda x: Some(x + 1)).unwrap() == 3
    assert nothing.and_then(lambda x: Some(x)) is nothing