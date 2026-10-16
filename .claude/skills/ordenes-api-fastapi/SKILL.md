---
name: ordenes-api-fastapi
description: Convenciones, arquitectura y plantillas de código para la API REST de órdenes de compra del reto técnico, hecha con Python 3.12 y FastAPI (máquina de estados, reglas RN-01 a RN-06, errores Problem Details, logging con X-Request-ID). Usa este skill siempre que escribas o modifiques código dentro de backend/app, agregues o cambies un endpoint, una regla de negocio, una excepción, un schema Pydantic o el repositorio de órdenes, aunque el usuario no mencione FastAPI de forma explícita.
---

# API de órdenes de compra con FastAPI

Este skill mantiene el backend coherente con las decisiones del reto. Los evaluadores revisan si el código respeta las reglas de negocio, si los errores son consistentes y si las decisiones están justificadas, así que no improvises convenciones distintas a las de aquí.

## Arquitectura

Hexagonal ligera. El dominio no importa nada de FastAPI ni de Pydantic, para que las reglas se prueben con tests unitarios puros (rápidos y buenos para mutation testing).

```
backend/
├── app/
│   ├── domain/          estado.py, excepciones.py, maquina_estados.py, orden.py
│   ├── application/     servicio_ordenes.py
│   ├── infrastructure/  repositorio.py (interfaz + implementación en memoria)
│   ├── api/             schemas.py, rutas.py, errores.py
│   ├── core/            logging.py (JSON + middleware X-Request-ID)
│   └── main.py          create_app()
├── tests/
├── requirements.txt         dependencias de ejecución
├── requirements-dev.txt     -r requirements.txt + pytest, hypothesis, mutmut, ruff…
└── pyproject.toml           solo configuración de herramientas
```

Dirección de dependencias: `api → application → domain`, `infrastructure → domain`. Nunca al revés.

## Reglas de negocio

| Regla | Qué exige | Dónde se aplica |
|---|---|---|
| RN-01 | Al menos un producto | `Orden.__post_init__` y `min_length=1` en el schema |
| RN-02 | Cantidad > 0 | `LineaProducto.__post_init__` y `gt=0` en el schema |
| RN-03 | Total calculado automáticamente | Propiedad `Orden.total`; el schema de entrada rechaza `total` |
| RN-04 | Una orden entregada no se cancela | `validar_transicion` (ENTREGADA es terminal) |
| RN-05 | No se envía sin pagar | `validar_transicion` (CREADA → ENVIADA) |
| RN-06 | Sin transiciones inválidas | `validar_transicion` con el diccionario `TRANSICIONES` |

Transiciones válidas:

```
CREADA  → PAGADA, CANCELADA
PAGADA  → ENVIADA, CANCELADA
ENVIADA → ENTREGADA, CANCELADA   (supuesto documentado: RN-04 solo prohíbe cancelar ENTREGADA)
ENTREGADA, CANCELADA → ninguna (terminales)
```

Orden de validación dentro de `validar_transicion`, que importa porque decide el código HTTP:
1. Estado origen terminal → `EstadoTerminalError` (409).
2. Destino ENVIADA desde CREADA → `PagoRequeridoError` (400).
3. Destino fuera de las transiciones permitidas → `TransicionInvalidaError` (409).

## Política de códigos HTTP

| Situación | Código | Excepción |
|---|---|---|
| Payload inválido, RN-01, RN-02 | 422 | `RequestValidationError` o `ValidacionOrdenError` |
| Enviar sin pagar (RN-05) | 400 | `PagoRequeridoError` |
| Estado terminal (RN-04) | 409 | `EstadoTerminalError` |
| Otra transición inválida (RN-06) | 409 | `TransicionInvalidaError` |
| Orden inexistente | 404 | `OrdenNoEncontradaError` |

Los errores de validación traen además `errores: [{campo, mensaje}]`, con el campo sin el prefijo `body` (por ejemplo `productos.0.cantidad`) y el mensaje en español. El frontend usa `campo` para mostrar cada error junto a su input.

Todas las respuestas de error usan `application/problem+json` (RFC 9457) con `type`, `title`, `status`, `detail`, `instance` y `codigo` (por ejemplo `"RN-05"`). El `codigo` es lo que conecta cada error con su regla, así que nunca lo omitas.

## Endpoints

| Método y ruta | Éxito | Notas |
|---|---|---|
| `POST /orders` | 201 | Devuelve la orden con `estado: CREADA` y header `Location: /orders/{id}` |
| `GET /orders/{id}` | 200 | 404 si no existe |
| `GET /orders` | 200 | Lista, más recientes primero; query opcionales `estado`, `limit` (1–100, por defecto 50), `offset` |
| `PATCH /orders/{id}/status` | 200 | Body `{"estado": "PAGADA"}` |
| `DELETE /orders/{id}` | 200 | Cancelación lógica: pasa a CANCELADA y devuelve la orden |
| `GET /health` | 200 | `{"status": "ok"}` para Docker y CI |

## Convenciones

- **Dinero en `int`** (pesos sin decimales). Nunca `float`.
- **Nombres del dominio en español** y JSON en camelCase con `alias_generator=to_camel` (`valor_unitario` ↔ `valorUnitario`).
- **`extra="forbid"`** en todos los schemas de entrada: si el cliente manda `total`, responde 422.
- **La respuesta incluye `transicionesPermitidas`**, para que el frontend muestre solo botones válidos.
- **`create_app()` como fábrica**: cada test crea una app nueva con su propio repositorio, sin estado compartido.
- **El servicio se inyecta** con `Depends(obtener_servicio)` leyendo `request.app.state.servicio`.
- **Log por transición**: `orden_id`, `desde`, `hacia` y `request_id`, en JSON.
- La app escucha en el puerto **8080**: `uvicorn app.main:app --host 0.0.0.0 --port 8080`.

## Buenas prácticas

Este backend sigue las buenas prácticas REST, SOLID, DRY y clean code del skill `buenas-practicas-ingenieria`. Léelo antes de diseñar un endpoint nuevo, refactorizar o revisar código. Dos rutas vienen fijadas por el enunciado y no se cambian aunque no sean REST puro: `PATCH /orders/{id}/status` y `DELETE /orders/{id}` como cancelación; ambas se justifican en el README.

## Plantillas de código

Lee `references/plantillas.md` cuando vayas a crear o reescribir cualquier archivo de `app/`. Tiene el código completo de dominio, repositorio, servicio, schemas, manejadores de error, logging y `main.py`, ya alineado con las tablas de arriba.

## Antes de dar por terminado un cambio

1. ¿La regla nueva o modificada tiene su test marcado con `@pytest.mark.rn("RN-xx")`? (skill `pytest-calidad`)
2. ¿Un error nuevo tiene excepción de dominio, código HTTP en la tabla y `codigo` en el Problem Details?
3. ¿El dominio sigue sin importar FastAPI ni Pydantic?
4. Si cambió una decisión (código HTTP, transición), ¿se actualizó el README o el ADR? (skill `qa-documentacion`)
