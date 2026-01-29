import pytest
import asyncio
from koruspy import Some, nothing, async_option, AsyncOption

# -----------------------
# Test AsyncOption pipeline
# -----------------------
async def fetch_data(x):
    # Simulate an async operation, return Some or nothing
    await asyncio.sleep(0.1)
    if x > 0:
        return Some(x * 2)
    return nothing
async def default_value():
    await asyncio.sleep(0.05)
    return 42

async def is_multiple_of_five(x):
    await asyncio.sleep(0.05)
    return x % 5 == 0
 # Em vez de lambda com sleep, use uma função async real:
async def async_cond(x):
    return x % 2 == 0

# Ou se quiser manter a lambda, use assim para garantir que o retorno é awaitable:
   
@pytest.mark.asyncio
async def test_async_option_pipeline():
    inputs = [3, 5, -1, 10]

    results = [async_option(fetch_data(i)) for i in inputs]

    final_results = []

    for r in results:
        val = await r.filter_async(is_multiple_of_five) \
                     .map_async(lambda x: x + 1) \
                     .unwrap_or_async(default_value)  # função passada
        final_results.append(val)

    # Garantir tamanho
    assert len(final_results) == 4

    # 3 -> 6 não múltiplo de 5 -> default 42
    assert final_results[0] == 42

    # 5 -> 10 múltiplo de 5 -> +1 = 11
    assert final_results[1] == 11

    # -1 -> nothing -> default 42
    assert final_results[2] == 42

    # 10 -> 20 múltiplo de 5 -> +1 = 21
    assert final_results[3] == 21

# -----------------------
# Test async_option map_async
# -----------------------
@pytest.mark.asyncio
async def test_async_option_map_async():
    val = async_option(fetch_data(5))  # Some(10)
    result = val.map_async(lambda x: x * 3)
    value = await result.unwrap_or_async(default_value)
    assert value == 30

@pytest.mark.asyncio
async def test_async_option_map_async_nothing():
    val = async_option(fetch_data(-1))  # nothing
    result = val.map_async(lambda x: x * 3)
    value = await result.unwrap_or_async(default_value)
    assert value == 42

# -----------------------
# Test async_option filter_async
# -----------------------
@pytest.mark.asyncio
async def test_async_option_filter_async_pass():
    val = async_option(fetch_data(5))  # Some(10)
    result = val.filter_async(lambda x: asyncio.sleep(0, result=(x % 2 == 0)))
    value = await result.unwrap_or_async(default_value)
    assert value == 10

@pytest.mark.asyncio
async def test_async_option_filter_async_fail():
    val = async_option(fetch_data(3))  # Some(6)
    result = val.filter_async(lambda x: asyncio.sleep(0, result=(x % 5 == 0)))
    value = await result.unwrap_or_async(default_value)
    assert value == 42

# -----------------------
# Test unwrap_orAsync lazy
# -----------------------
@pytest.mark.asyncio
async def test_async_option_unwrap_orAsync_lazy():
    val = async_option(fetch_data(-1))  # nothing
    value = await val.unwrap_or_async(lambda: default_value())
    assert value == 42