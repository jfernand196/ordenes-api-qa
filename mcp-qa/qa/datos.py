"""Payloads de prueba derivados del schema real de la API (OrdenIn y ProductoIn)."""

from copy import deepcopy
from typing import Any, Literal

from app.api.schemas import OrdenIn, ProductoIn

Tipo = Literal["validos", "frontera", "invalidos"]


def _limite(modelo: type[OrdenIn] | type[ProductoIn], campo: str, atributo: str) -> int:
    """Lee una restricción (gt, min_length) del Field del schema, sin copiarla a mano."""
    for restriccion in modelo.model_fields[campo].metadata:
        valor = getattr(restriccion, atributo, None)
        if isinstance(valor, int):
            return valor
    raise LookupError(f"{modelo.__name__}.{campo} no define {atributo}")


def _alias(campo: str) -> str:
    return ProductoIn.model_fields[campo].alias or campo


def _base() -> dict[str, Any]:
    producto = {_alias("id"): "P001", _alias("cantidad"): 1, _alias("valor_unitario"): 1000}
    return {"cliente": "Cliente de prueba", "productos": [producto]}


def _con_producto(**cambios: Any) -> dict[str, Any]:
    payload = _base()
    payload["productos"][0].update({_alias(k): v for k, v in cambios.items()})
    return payload


def _caso(
    descripcion: str, payload: dict[str, Any], status: int, campo: str | None = None
) -> dict[str, Any]:
    caso: dict[str, Any] = {
        "descripcion": descripcion,
        "payload": payload,
        "status_esperado": status,
    }
    if campo is not None:
        caso["campo_con_error"] = campo
    return caso


def generar(tipo: Tipo) -> list[dict[str, Any]]:
    gt_cantidad = _limite(ProductoIn, "cantidad", "gt")
    gt_valor = _limite(ProductoIn, "valor_unitario", "gt")
    min_productos = _limite(OrdenIn, "productos", "min_length")
    cantidad, valor = _alias("cantidad"), _alias("valor_unitario")

    if tipo == "validos":
        varios = _base()
        varios["productos"].append(deepcopy(varios["productos"][0]) | {_alias("id"): "P002"})
        return [
            _caso("Orden mínima válida", _base(), 201),
            _caso("Orden con dos productos", varios, 201),
        ]
    if tipo == "frontera":
        sin_productos = _base()
        sin_productos["productos"] = sin_productos["productos"][: min_productos - 1]
        return [
            _caso(
                f"Cantidad en el límite ({gt_cantidad})",
                _con_producto(cantidad=gt_cantidad),
                422,
                f"productos.0.{cantidad}",
            ),
            _caso(
                f"Cantidad justo sobre el límite ({gt_cantidad + 1})",
                _con_producto(cantidad=gt_cantidad + 1),
                201,
            ),
            _caso(
                f"Valor unitario en el límite ({gt_valor})",
                _con_producto(valor_unitario=gt_valor),
                422,
                f"productos.0.{valor}",
            ),
            _caso(
                f"Valor unitario justo sobre el límite ({gt_valor + 1})",
                _con_producto(valor_unitario=gt_valor + 1),
                201,
            ),
            _caso(
                f"Menos productos que el mínimo ({min_productos - 1})",
                sin_productos,
                422,
                "productos",
            ),
        ]
    sin_cliente = _base()
    del sin_cliente["cliente"]
    return [
        _caso("Total enviado por el cliente (RN-03)", _base() | {"total": 1}, 422, "total"),
        _caso(
            "Cantidad negativa (RN-02)",
            _con_producto(cantidad=gt_cantidad - 1),
            422,
            f"productos.0.{cantidad}",
        ),
        _caso("Sin cliente", sin_cliente, 422, "cliente"),
        _caso(
            "Cantidad que no es un número",
            _con_producto(cantidad="dos"),
            422,
            f"productos.0.{cantidad}",
        ),
    ]
