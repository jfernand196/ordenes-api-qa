---
name: qa-documentacion
description: Plantillas y criterios para la documentación del reto técnico de órdenes de compra (README con todas las secciones que exige el enunciado, estrategia de pruebas basada en riesgo (docs/TEST_STRATEGY.md), ADR, uso responsable de IA (docs/AI_USAGE.md), evidencias y matriz de trazabilidad generada automáticamente con scripts/generar_trazabilidad.py). Usa este skill siempre que escribas o edites el README, cualquier archivo en docs/, la sección de supuestos o decisiones técnicas, o el usuario hable de documentación, evidencias, trazabilidad, matriz de riesgo, pirámide de pruebas, ADR o la entrega final.
---

# Documentación, estrategia de pruebas y trazabilidad

El enunciado dice que valoran "cómo piensas la calidad" y la "capacidad para justificar decisiones técnicas". La documentación es donde eso se ve. Un evaluador con poco tiempo lee el README primero: tiene que poder entender la solución, ejecutarla y ver las evidencias sin abrir el código.

## Archivos

```
README.md
docs/
├── TEST_STRATEGY.md      riesgo, pirámide, qué nivel cubre qué
├── TRACEABILITY.md       generado por el script; no se edita a mano
├── AI_USAGE.md           qué hizo la IA, qué se revisó, qué se descartó
├── adr/
│   ├── 001-arquitectura-hexagonal.md
│   ├── 002-persistencia-en-memoria.md
│   └── 003-politica-codigos-http.md
└── evidence/             capturas: cobertura, mutation, Karate, Playwright, pipeline
scripts/
└── generar_trazabilidad.py   (copiar desde este skill a la raíz del repo)
```

Plantillas completas en `references/plantillas.md`. Léelas antes de escribir cualquiera de estos documentos.

## README: secciones obligatorias

El enunciado exige, como mínimo: descripción de la solución, arquitectura utilizada, decisiones técnicas, cómo ejecutar la aplicación, cómo ejecutar las pruebas, evidencia de cobertura, evidencia de mutation testing y evidencia del pipeline ejecutado. La plantilla trae todas, en ese orden, más supuestos, tabla de códigos HTTP, mutantes aceptados y trazabilidad.

Reglas de escritura:
- **Cada decisión con su porqué** en una o dos frases, y enlace al ADR si existe.
- **Supuestos explícitos** donde el enunciado es ambiguo (ENVIADA → CANCELADA, 400 vs 409, DELETE lógico). Es mejor declarar un supuesto que dejar al evaluador adivinando.
- **Comandos copiables** para Windows (PowerShell) y Linux cuando difieran.
- **Evidencias como imágenes en `docs/evidence/`** más el enlace a una ejecución real del pipeline. Las cifras en el README (cobertura, mutation score) deben coincidir con las capturas.
- **Escribe el README por partes**, al terminar cada bloque de trabajo, no todo el último día.

## Estrategia de pruebas basada en riesgo

`TEST_STRATEGY.md` justifica dónde se pusieron más pruebas. Estructura:
1. Matriz de riesgo: riesgo, probabilidad, impacto, nivel resultante y mitigación (qué pruebas lo cubren).
2. Pirámide: cuántas pruebas hay por nivel y por qué esa proporción.
3. Qué no se probó y por qué (por ejemplo, rendimiento o seguridad avanzada), dicho con honestidad.
4. Quality gates y umbrales.

Los riesgos más altos del reto son las transiciones de estado (RN-04, RN-05, RN-06) y el cálculo del total (RN-03): impacto económico directo.

## Trazabilidad

`scripts/generar_trazabilidad.py` recorre los markers `@pytest.mark.rn("RN-xx")`, los tags `@RN-xx` de Karate y los tags de Playwright, y escribe una tabla regla → pruebas por nivel.

```bash
python scripts/generar_trazabilidad.py --salida docs/TRACEABILITY.md
python scripts/generar_trazabilidad.py --estricto   # código 1 si una regla queda sin pruebas
```

En CI corre en el job de lint con `--estricto` y publica la tabla en el resumen del pipeline (skill `docker-cicd-quality-gates`). Si agregas una regla nueva, agrégala al diccionario `REGLAS` del script.

## Uso responsable de IA

`AI_USAGE.md` es corto y concreto: herramientas usadas, para qué tareas, qué revisaste a mano y un par de ejemplos de sugerencias que corregiste o descartaste y por qué. Eso demuestra criterio, que es lo que evalúan; no basta con decir "usé IA".

## Antes de entregar

- [ ] Clon limpio en otra carpeta: el README funciona tal cual.
- [ ] Las cifras del README coinciden con el último pipeline en verde.
- [ ] `docs/TRACEABILITY.md` regenerado.
- [ ] Capturas en `docs/evidence/` y enlazadas.
- [ ] `CHANGELOG.md` y tag `v1.0.0`.
