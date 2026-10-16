import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.domain.estado import Estado
from app.domain.excepciones import EstadoTerminalError, ValidacionOrdenError
from app.domain.orden import LineaProducto, Orden


def linea(cantidad: int = 1, valor: int = 1000, id_: str = "P001") -> LineaProducto:
    return LineaProducto(id=id_, cantidad=cantidad, valor_unitario=valor)


@pytest.mark.rn("RN-01")
def test_una_orden_sin_productos_es_invalida():
    with pytest.raises(ValidacionOrdenError) as exc:
        Orden(cliente="Ana", productos=[])
    assert exc.value.codigo == "RN-01"


@pytest.mark.rn("RN-01")
def test_una_orden_con_un_producto_es_valida():
    assert Orden(cliente="Ana", productos=[linea()]).estado == Estado.CREADA


@pytest.mark.rn("RN-02")
@pytest.mark.parametrize("cantidad", [-1, 0])
def test_cantidad_no_positiva_es_invalida(cantidad):
    with pytest.raises(ValidacionOrdenError) as exc:
        linea(cantidad=cantidad)
    assert exc.value.codigo == "RN-02"


@pytest.mark.rn("RN-02")
def test_cantidad_uno_es_valida():
    assert linea(cantidad=1).cantidad == 1


@pytest.mark.parametrize("valor", [-1, 0])
def test_valor_unitario_no_positivo_es_invalido(valor):
    with pytest.raises(ValidacionOrdenError):
        linea(valor=valor)


def test_valor_unitario_uno_es_valido():
    assert linea(valor=1).valor_unitario == 1


@pytest.mark.parametrize("cliente", ["", "   "])
def test_cliente_vacio_es_invalido(cliente):
    with pytest.raises(ValidacionOrdenError):
        Orden(cliente=cliente, productos=[linea()])


def test_id_de_producto_vacio_es_invalido():
    with pytest.raises(ValidacionOrdenError):
        linea(id_=" ")


@pytest.mark.rn("RN-03")
def test_total_del_ejemplo_del_enunciado():
    orden = Orden(cliente="Juan Pérez", productos=[linea(cantidad=2, valor=100000)])
    assert orden.total == 200000


@pytest.mark.rn("RN-03")
def test_total_con_varios_productos():
    orden = Orden(cliente="Ana", productos=[linea(2, 1500, "P1"), linea(3, 200, "P2")])
    assert orden.total == 3600


@pytest.mark.rn("RN-03")
@given(
    st.lists(st.tuples(st.integers(1, 1_000), st.integers(1, 10_000_000)), min_size=1, max_size=20)
)
def test_total_es_la_suma_de_cantidad_por_valor(items):
    productos = [linea(c, v, f"P{i}") for i, (c, v) in enumerate(items)]
    assert Orden(cliente="Ana", productos=productos).total == sum(c * v for c, v in items)


@pytest.mark.rn("RN-04")
def test_cancelar_desde_entregada_no_cambia_el_estado():
    orden = Orden(cliente="Ana", productos=[linea()])
    for estado in (Estado.PAGADA, Estado.ENVIADA, Estado.ENTREGADA):
        orden.cambiar_estado(estado)
    with pytest.raises(EstadoTerminalError):
        orden.cancelar()
    assert orden.estado == Estado.ENTREGADA


def test_cambiar_estado_devuelve_el_estado_anterior():
    orden = Orden(cliente="Ana", productos=[linea()])
    assert orden.cambiar_estado(Estado.PAGADA) == Estado.CREADA
    assert orden.estado == Estado.PAGADA


def test_transiciones_permitidas_de_una_orden_nueva():
    orden = Orden(cliente="Ana", productos=[linea()])
    assert orden.transiciones_permitidas == [Estado.CANCELADA, Estado.PAGADA]


def test_cada_orden_tiene_un_id_distinto():
    a = Orden(cliente="Ana", productos=[linea()])
    b = Orden(cliente="Ana", productos=[linea()])
    assert a.id != b.id


def test_el_estado_no_se_puede_asignar_saltandose_la_maquina_de_estados():
    orden = Orden(cliente="Ana", productos=[linea()])
    with pytest.raises(AttributeError):
        orden.estado = Estado.ENTREGADA
    assert orden.estado == Estado.CREADA


@pytest.mark.rn("RN-01")
def test_los_productos_no_cambian_aunque_cambie_la_lista_original():
    lineas = [linea()]
    orden = Orden(cliente="Ana", productos=lineas)
    lineas.clear()
    assert len(orden.productos) == 1
    assert isinstance(orden.productos, tuple)


def test_la_orden_conserva_el_cliente():
    assert Orden(cliente="Juan Pérez", productos=[linea()]).cliente == "Juan Pérez"
