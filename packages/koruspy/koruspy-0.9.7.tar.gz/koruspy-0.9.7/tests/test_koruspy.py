import pytest
from koruspy import SomeList, LazyList, Some, nothing, Okay, Err, OptionUnwrapError

# --- Testes para SomeList ---

def test_somelist_basic_ops():
    sl = SomeList([1, 2, 3])
    assert len(sl) == 3
    # No seu código o método é finalize()
    assert sl.head().finalize() == 1 
    assert sl.last().finalize() == 3
    assert sl.sum() == 6

def test_somelist_safety():
    # Caso 1: Lista com um 'nothing' deve retornar o objeto global 'nothing'
    sl_with_nothing = SomeList([Some(10), nothing, Some(20)])
    res = sl_with_nothing.unwrap_list()
    assert res is nothing 
    
    # Se tentarmos finalizar o que é 'nothing', deve estourar o OptionUnwrapError
    with pytest.raises(OptionUnwrapError):
        res.finalize()

    # Caso 2: Lista limpa deve retornar Some([10, 20])
    sl_clean = SomeList([Some(10), Some(20)])
    res_clean = sl_clean.unwrap_list()
    assert res_clean.finalize() == [10, 20]


# --- Testes para LazyList (Correção do Drop) ---

def test_lazylist_drop_and_take():
    lazy = LazyList(lambda: (i for i in range(10)))
    # Corrija o método drop no seu arquivo Option.py conforme abaixo
    res = list(lazy.drop(5).take(2))
    assert res == [5, 6]
