import pytest
from koruspy import Some, SomeList, nothing


class TestSomeListV9:
    
    # --- TESTES DE INICIALIZAÇÃO ---
    
    def test_init_with_mixed_values(self):
        """Garante que tudo vira Some na entrada"""
        sl = SomeList([1, nothing, "texto"])
        assert isinstance(sl.value[0], Some)
        assert sl.value[0].value == 1
        assert sl.value[1] is nothing
        assert sl.value[2].value == "texto"

    def test_init_single_value(self):
        """Garante que valor único vira lista de um Some"""
        sl = SomeList(10)
        assert sl.value == [Some(10)]

    def test_init_from_some(self):
        """Garante que SomeList(Some(x)) desempacota corretamente"""
        sl = SomeList(Some(5))
        assert sl.value == [Some(5)]

    # --- TESTES DE FUNCIONALIDADE ---

    def test_map_logic(self):
        """Testa se o map aplica a função no .value e mantém o Some"""
        sl = SomeList([1, 2])
        result = sl.map(lambda x: x * 2)
        assert result.value == [Some(2), Some(4)]

    def test_map_with_nothing(self):
        """Verifica se o nothing é imune ao map (se você aplicou minha dica)"""
        sl = SomeList([1, nothing])
        result = sl.map(lambda x: x + 1)
        assert result.value[1] is nothing

    def test_map_exception(self):
        """Agora o map deve estourar o erro original (Performance > Silêncio)"""
        sl = SomeList([1, 2])
        with pytest.raises(ZeroDivisionError):
            sl.map(lambda x: x / 0)

    # --- TESTES DE CONVERSÃO E FILTRO ---

    def test_to_integerlist(self):
        sl = SomeList([1.5, "2", 3])
        res = sl.to_integerlist()
        assert res.value == [Some(1), Some(2), Some(3)]

    def test_filter_nothing(self):
        sl = SomeList([1, nothing, 2, None])
        # Note: None vira Some(None), então filter_nothing remove apenas o 'nothing' global
        res = sl.filter_nothing()
        assert nothing not in res.value
        assert len(res.value) == 2  # 1, 2 e Some(None)

    # --- TESTES DE SOMA E AGREGAÇÃO ---

    def test_sum_integration(self):
        """Testa a soma ignorando o que não é número e tratando o nothing"""
        sl = SomeList([10, "lixo", nothing, 5.5])
        assert sl.sum() == 15.5

    def test_unwrap_list(self):
        """Testa se consegue extrair os valores puros de volta"""
        sl = SomeList([1, 2, 3])
        assert sl.unwrap_list().value == [1, 2, 3]
        
        sl_with_nothing = SomeList([1, nothing])
        assert sl_with_nothing.unwrap_list() is nothing
