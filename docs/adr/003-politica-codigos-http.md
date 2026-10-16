# ADR-003: Política de códigos HTTP y formato de errores

- Estado: aceptada
- Fecha: 2026-10-15

## Contexto

El enunciado fija dos códigos en sus escenarios de aceptación: **400** al enviar una orden no pagada y **409** al cancelar una orden entregada. Hacía falta una política coherente para el resto de errores y un formato único.

## Decisión

| Situación | Código | `codigo` |
|---|---|---|
| Payload inválido (RN-01, RN-02, total enviado) | 422 | `VALIDACION` |
| Precondición de pago incumplida (RN-05) | 400 | `RN-05` |
| Orden en estado terminal (RN-04) | 409 | `RN-04` |
| Transición inválida (RN-06) | 409 | `RN-06` |
| Orden inexistente | 404 | `NO_ENCONTRADA` |

Todos los errores usan **Problem Details (RFC 9457)**, con `content-type: application/problem+json` y un campo `codigo` que enlaza el error con su regla. Los errores de validación incluyen `errores: [{campo, mensaje}]`, con el campo sin el prefijo `body` y el mensaje en español, para que la interfaz los muestre junto a cada input.

## Alternativas consideradas

- **400 para todos los errores:** más simple, pero el consumidor no podría distinguir un dato inválido de un conflicto con el estado actual.
- **Formato de error propio:** funcionaría, pero Problem Details es un estándar conocido.

## Consecuencias

- El contrato de error es uniforme y cada error es trazable a su regla.
- Los mensajes de Pydantic se traducen al español en un solo lugar (`app/api/errores.py`).
- Los códigos están documentados en OpenAPI (`/docs`) para cada endpoint.
