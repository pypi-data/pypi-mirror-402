import pytest
import asyncio
from koruspy import Some, nothing, async_option, AsyncOption

# --- Simuladores de Operações Reais ---

async def db_find_user(user_id):
    """Simula busca no banco: ID 1 existe, outros não."""
    await asyncio.sleep(0.01)
    if user_id == 1:
        return Some({"id": 1, "name": "Koruspy Dev", "admin": True})
    return nothing

async def log_success(user):
    """Efeito colateral para sucesso."""
    await asyncio.sleep(0.01)
    return f"Log: Usuário {user} processado."

async def log_failure():
    """Efeito colateral para falha."""
    await asyncio.sleep(0.01)
    return "Log: Tentativa de acesso inválida."

# --- O Mega Teste ---

@pytest.mark.asyncio
async def test_full_async_pipeline_with_new_features():
    # 1. TESTE COM SUCESSO
    success_tracker = []
    
    res_success = await (
        async_option(db_find_user(1))
        .filter_async(lambda u: u["admin"] is True)
        .map_async(lambda u: u["name"].upper())
        .if_present_async(lambda name: success_tracker.append(f"Presente: {name}"))
        .if_present_async(log_success) # Testa se aguarda corrotina do log
        .on_nothing_async(log_failure)  # Não deve rodar
        .unwrap_or_async("Desconhecido")
    )

    assert res_success == "KORUSPY DEV"
    assert "Presente: KORUSPY DEV" in success_tracker
    
    # 2. TESTE COM FALHA (on_nothing_async)
    failure_tracker = []

    res_failure = await (
        async_option(db_find_user(99)) # Retorna nothing
        .if_present_async(lambda x: failure_tracker.append("Não devia estar aqui"))
        .on_nothing_async(lambda: failure_tracker.append("Nada encontrado"))
        .on_nothing_async(log_failure) # Testa se aguarda corrotina de falha
        .unwrap_or_async(lambda: asyncio.sleep(0.01, result="Fallback Assíncrono"))
    )

    assert res_failure == "Fallback Assíncrono"
    assert "Nada encontrado" in failure_tracker
    assert "Não devia estar aqui" not in failure_tracker

@pytest.mark.asyncio
async def test_async_option_direct_values():
    """Testa se as funções aceitam valores diretos em vez de callables."""
    # Teste if_present_async com valor direto (raro, mas deve suportar)
    await async_option(asyncio.sleep(0.01, result=Some("valor"))) \
        .if_present_async(print("Isso roda imediatamente, mas a função deve lidar"))

    # Teste unwrap_or_async com valor direto
    val = await async_option(asyncio.sleep(0.01, result=nothing)) \
        .unwrap_or_async("Valor Direto")
    
    assert val == "Valor Direto"
    