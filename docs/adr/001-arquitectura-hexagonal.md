# ADR-001: Arquitectura hexagonal ligera

- Estado: aceptada
- Fecha: 2026-10-15

## Contexto

Las reglas de negocio (RN-01 a RN-06) son el corazón del reto y deben probarse a fondo, incluido mutation testing. Si la lógica vive en los endpoints, cada prueba necesita levantar HTTP y el mutation testing se vuelve lento y ruidoso.

## Decisión

Separar el backend en capas con dependencias en una sola dirección:

- `domain`: entidades, máquina de estados y excepciones, sin FastAPI ni Pydantic.
- `application`: servicio que orquesta los casos de uso y depende de la interfaz `OrderRepository`.
- `infrastructure`: implementación del repositorio.
- `api`: endpoints, schemas y traducción de excepciones a HTTP.

Dirección de dependencias: `api → application → domain` e `infrastructure → domain`.

## Alternativas consideradas

- **Lógica en los endpoints:** menos archivos, pero las reglas solo se podrían probar por HTTP y el mutation testing mutaría también código de framework.
- **Arquitectura hexagonal completa** (puertos y adaptadores para todo): demasiada ceremonia para cinco endpoints.

## Consecuencias

- Las reglas se prueban con pruebas unitarias puras: 76 pruebas en unos 2 segundos.
- El mutation testing se limita a dominio y aplicación, donde están las reglas, y llega a 100 %.
- Hay algo de código de mapeo entre schemas y entidades (`OrdenOut.desde_dominio`).
