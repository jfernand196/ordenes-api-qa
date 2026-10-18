import pytest
from mcp import Client

from servidor import mcp


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_expone_las_cuatro_herramientas():
    async with Client(mcp, raise_exceptions=True) as cliente:
        resultado = await cliente.list_tools()
    assert {h.name for h in resultado.tools} == {
        "reglas_de_negocio",
        "matriz_trazabilidad",
        "transiciones_sin_aceptacion",
        "datos_de_prueba",
    }


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("herramienta", "argumentos"),
    [
        ("reglas_de_negocio", {}),
        ("matriz_trazabilidad", {"regla": "RN-05"}),
        ("transiciones_sin_aceptacion", {}),
        ("datos_de_prueba", {"tipo": "invalidos"}),
    ],
)
async def test_cada_herramienta_responde_por_el_protocolo(herramienta, argumentos):
    async with Client(mcp, raise_exceptions=True) as cliente:
        resultado = await cliente.call_tool(herramienta, argumentos)
    assert not resultado.is_error
    assert resultado.structured_content
