# Plantillas de Docker y CI/CD

Contenido:
1. backend/Dockerfile y .dockerignore
2. docker-compose.yml
3. .github/workflows/ci.yml

---

## 1. Backend

### Dockerfile (raíz del repositorio)
```dockerfile
# Imagen de la API. Vive en la raíz para que funcione el comando del enunciado:
#   docker build -t challenge-api .
# docker-compose y el CI usan este mismo archivo (una sola receta).
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

FROM base AS dependencias
COPY backend/requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

FROM base AS ejecucion
COPY --from=dependencias /install /usr/local
COPY backend/app ./app
RUN useradd --create-home --uid 10001 appuser
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health').status == 200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
```

### .dockerignore (raíz del repositorio)
```text
# Contexto de build de la API (Dockerfile en la raíz). Lista de permitidos:
# se excluye todo y solo entra lo que la imagen necesita.
*
!backend/requirements.txt
!backend/app/
**/__pycache__
**/*.pyc
```

---

## 2. docker-compose.yml (raíz del repo)

```yaml
services:
  api:
    build: .
    image: challenge-api
    ports:
      - "8080:8080"
    environment:
      LOG_LEVEL: INFO
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 5s

  web:
    build: ./frontend
    image: challenge-web
    ports:
      - "3000:80"
    depends_on:
      api:
        condition: service_healthy
```

Comandos:
```bash
docker compose up -d --build --wait   # levanta todo y espera healthchecks
docker compose logs -f api            # logs JSON de la API
docker compose down                   # apaga
```

---

## 3. .github/workflows/ci.yml

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

env:
  PYTHON_VERSION: "3.12"

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
          cache-dependency-path: backend/requirements-dev.txt
      - run: pip install -r requirements-dev.txt
      - name: Ruff (errores y formato)
        run: |
          ruff check .
          ruff format --check .
      - name: Trazabilidad (todas las reglas con pruebas y matriz al día)
        working-directory: .
        run: |
          python scripts/generar_trazabilidad.py --salida docs/TRACEABILITY.md --estricto
          git diff --exit-code docs/TRACEABILITY.md || { echo "::error::docs/TRACEABILITY.md está desactualizado. Ejecuta scripts/generar_trazabilidad.py y haz commit."; exit 1; }
          cat docs/TRACEABILITY.md >> "$GITHUB_STEP_SUMMARY"
  unit-tests:
    name: Pruebas unitarias e integración con cobertura
    needs: lint
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
          cache-dependency-path: backend/requirements-dev.txt
      - run: pip install -r requirements-dev.txt
      - name: Pytest con cobertura (quality gate >= 80 %)
        run: >
          pytest --cov=app --cov-branch
          --cov-report=term-missing --cov-report=xml --cov-report=html
          --junitxml=reports/junit.xml
      - name: Resumen de cobertura
        if: always()
        run: |
          echo "### Cobertura" >> "$GITHUB_STEP_SUMMARY"
          coverage report --format=markdown >> "$GITHUB_STEP_SUMMARY" || true
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: cobertura
          path: |
            backend/htmlcov
            backend/coverage.xml
            backend/reports/junit.xml
  mutation:
    name: Mutation testing (quality gate >= 70 %)
    needs: unit-tests
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
          cache-dependency-path: backend/requirements-dev.txt
      - run: pip install -r requirements-dev.txt
      - name: Ejecutar mutmut
        # Quien decide es el quality gate de abajo, que también falla si no hay estadísticas.
        run: mutmut run || echo "mutmut terminó con código $?"
      - name: Exportar resultados
        if: always()
        run: |
          mkdir -p reports
          mutmut export-cicd-stats
          mutmut results > reports/mutmut-results.txt || true
      - name: Quality gate (>= 70 %)
        run: python scripts/check_mutation_score.py --umbral 70
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: mutation
          path: |
            backend/mutants/mutmut-cicd-stats.json
            backend/reports/mutmut-results.txt
  docker-build:
    name: Construcción de imagen Docker
    needs: unit-tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build de la imagen (comando del enunciado)
        run: docker build -t challenge-api:${{ github.sha }} .
      - name: Prueba de humo con docker compose
        run: |
          docker compose up -d --build --wait
          curl -fsS http://localhost:8080/health
          curl -fsS -X POST http://localhost:8080/orders \
            -H "Content-Type: application/json" \
            -d '{"cliente":"CI","productos":[{"id":"P1","cantidad":1,"valorUnitario":1000}]}'
          curl -fsS http://localhost:3000/ | grep -q 'id="root"'
          curl -fsS http://localhost:3000/api/health
      - name: Logs de la API
        if: always()
        run: docker compose logs api
      - name: Apagar
        if: always()
        run: docker compose down
  acceptance:
    name: Pruebas de aceptación (Karate)
    needs: unit-tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "17"
          cache: maven
      - name: Levantar la API
        run: docker compose up -d --build --wait
      - name: Karate
        run: mvn -B test -f acceptance-tests/pom.xml -DbaseUrl=http://localhost:8080
      - name: Logs de la API
        if: always()
        run: |
          mkdir -p reports
          docker compose logs api > reports/api-karate.log
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: karate
          path: |
            acceptance-tests/target/karate-reports
            reports/api-karate.log
      - name: Apagar
        if: always()
        run: docker compose down

  frontend:
    name: Frontend (tipos, pruebas y build)
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "24"
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npm run typecheck
      - run: npm test -- --run
      - run: npm run build

  e2e:
    name: Pruebas E2E (Playwright)
    needs: [frontend, unit-tests]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "24"
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - name: Levantar API y web
        run: docker compose up -d --build --wait
      - name: Instalar dependencias y Chromium
        working-directory: frontend
        run: |
          npm ci
          npx playwright install --with-deps chromium
      - name: Playwright
        working-directory: frontend
        run: npx playwright test
      - name: Logs de la API y la web
        if: always()
        run: |
          mkdir -p reports
          docker compose logs > reports/stack-e2e.log
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright
          path: |
            frontend/playwright-report
            frontend/test-results
            reports/stack-e2e.log
      - name: Apagar
        if: always()
        run: docker compose down
```

Notas:
- `mutmut export-cicd-stats` existe desde mutmut 3.x; si la versión instalada no lo tiene, actualiza mutmut antes de cambiar el script.
- El gate de cobertura vive en `pyproject.toml` (`fail_under = 80`), por eso el paso de pytest no repite `--cov-fail-under`.
- SonarCloud es opcional en el enunciado; si sobra tiempo se agrega como un job que lee `coverage.xml`.
