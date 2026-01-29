import pytest
from koruspy import Some, FrozenSomeList, SomeList, nothing


def test_frozen_some_list_is_hashable():
    a = FrozenSomeList([Some(1), Some(2)])
    b = FrozenSomeList([Some(1), Some(2)])

    assert hash(a) == hash(b)


def test_frozen_some_list_equality():
    a = FrozenSomeList([Some(1), Some(2)])
    b = FrozenSomeList([Some(1), Some(2)])
    c = FrozenSomeList([Some(2), Some(1)])

    assert a == b
    assert a != c


def test_frozen_some_list_is_immutable():
    fs = FrozenSomeList([Some(1)])

    with pytest.raises(TypeError):
        fs[0] = Some(2)    

def test_frozen_some_list_behaves_like_sequence():
    fs = FrozenSomeList([Some(1), Some(2)])

    assert len(fs) == 2
    assert fs[0] == Some(1)
    assert list(fs) == [Some(1), Some(2)]


def test_some_hashable_value():
    s = Some(10)
    assert isinstance(hash(s), int)


def test_some_unhashable_value_raises():
    s = Some([1, 2, 3])
    with pytest.raises(TypeError):
        hash(s)


def test_some_equality():
    assert Some(10) == Some(10)
    assert Some(10) != Some(20)


def test_some_not_equal_to_raw_value():
    assert Some(10) != 10


def test_frozen_somelist_with_nothing_hashable():
    a = FrozenSomeList([Some(1), nothing])
    b = FrozenSomeList([Some(1), nothing])

    assert a == b
    assert hash(a) == hash(b)

    d = {a: "ok"}
    assert d[b] == "ok"