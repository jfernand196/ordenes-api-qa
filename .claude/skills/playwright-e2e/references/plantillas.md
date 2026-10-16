# Plantillas de Playwright

Contenido:
1. playwright.config.ts
2. Datos por API
3. Page Objects
4. Specs de los 4 flujos

---

## 1. frontend/playwright.config.ts

```ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [
    ['list'],
    ['html', { open: 'never' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
  ],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:3000',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
```

---

## 2. frontend/e2e/datos.ts

Usa el mismo `baseURL` que la web y pasa por el proxy `/api` de nginx, así no hace falta una segunda URL.

```ts
import type { APIRequestContext } from '@playwright/test';

export type Estado = 'CREADA' | 'PAGADA' | 'ENVIADA' | 'ENTREGADA' | 'CANCELADA';

export interface OrdenCreada {
  id: string;
  cliente: string;
}

export async function crearOrdenPorApi(
  request: APIRequestContext,
  cliente = `Cliente E2E ${Date.now()}`,
): Promise<OrdenCreada> {
  const respuesta = await request.post('/api/orders', {
    data: { cliente, productos: [{ id: 'P001', cantidad: 2, valorUnitario: 50000 }] },
  });
  if (!respuesta.ok()) {
    throw new Error(`No se pudo crear la orden: ${respuesta.status()} ${await respuesta.text()}`);
  }
  return (await respuesta.json()) as OrdenCreada;
}

export async function llevarA(request: APIRequestContext, id: string, ...estados: Estado[]) {
  for (const estado of estados) {
    const respuesta = await request.patch(`/api/orders/${id}/status`, { data: { estado } });
    if (!respuesta.ok()) {
      throw new Error(`No se pudo pasar a ${estado}: ${respuesta.status()} ${await respuesta.text()}`);
    }
  }
}
```

---

## 3. Page Objects

### frontend/e2e/paginas/ListadoPage.ts
```ts
import type { Locator, Page } from '@playwright/test';

export class ListadoPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async abrir() {
    await this.page.goto('/');
  }

  fila(id: string): Locator {
    return this.page.getByTestId(`fila-orden-${id}`);
  }

  async filtrarPor(estado: string) {
    await this.page.getByTestId('filtro-estado').selectOption(estado);
  }

  async abrirOrden(id: string) {
    await this.fila(id).getByRole('link').click();
  }

  async irANuevaOrden() {
    await this.page.getByTestId('btn-nueva-orden').click();
  }
}
```

### frontend/e2e/paginas/NuevaOrdenPage.ts
```ts
import type { Locator, Page } from '@playwright/test';

export interface ProductoFormulario {
  id: string;
  cantidad: number;
  valorUnitario: number;
}

export class NuevaOrdenPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async abrir() {
    await this.page.goto('/ordenes/nueva');
  }

  get total(): Locator {
    return this.page.getByTestId('total-orden');
  }

  get mensajeError(): Locator {
    return this.page.getByTestId('mensaje-error');
  }

  async llenar(cliente: string, productos: ProductoFormulario[]) {
    await this.page.getByTestId('input-cliente').fill(cliente);
    for (const [i, p] of productos.entries()) {
      if (i > 0) await this.page.getByTestId('btn-agregar-producto').click();
      await this.page.getByTestId(`input-producto-id-${i}`).fill(p.id);
      await this.page.getByTestId(`input-cantidad-${i}`).fill(String(p.cantidad));
      await this.page.getByTestId(`input-valor-${i}`).fill(String(p.valorUnitario));
    }
  }

  async enviar() {
    await this.page.getByTestId('btn-crear-orden').click();
  }
}
```

### frontend/e2e/paginas/DetallePage.ts
```ts
import type { Locator, Page } from '@playwright/test';
import type { Estado } from '../datos';

export class DetallePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async abrir(id: string) {
    await this.page.goto(`/ordenes/${id}`);
  }

  get estado(): Locator {
    return this.page.getByTestId('estado-orden');
  }

  get botonCancelar(): Locator {
    return this.page.getByTestId('btn-cancelar-orden');
  }

  botonEstado(estado: Estado): Locator {
    return this.page.getByTestId(`btn-estado-${estado}`);
  }

  async cambiarEstadoA(estado: Estado) {
    await this.botonEstado(estado).click();
  }

  async cancelar() {
    this.page.once('dialog', (dialogo) => dialogo.accept());
    await this.botonCancelar.click();
  }
}
```

---

## 4. frontend/e2e/ordenes.spec.ts

Deja `{ tag: [...] }` como segundo argumento de `test(...)`: el script de trazabilidad lo busca ahí.

```ts
import { expect, test } from '@playwright/test';
import { crearOrdenPorApi, llevarA } from './datos';
import { DetallePage } from './paginas/DetallePage';
import { ListadoPage } from './paginas/ListadoPage';
import { NuevaOrdenPage } from './paginas/NuevaOrdenPage';

test.describe('Gestión de órdenes de compra', () => {
  test('crear una orden desde el formulario', { tag: ['@smoke', '@RN-03'] }, async ({ page }) => {
    const nueva = new NuevaOrdenPage(page);
    await nueva.abrir();
    await nueva.llenar('Juan Pérez E2E', [
      { id: 'P001', cantidad: 2, valorUnitario: 100000 },
      { id: 'P002', cantidad: 1, valorUnitario: 50000 },
    ]);
    await expect(nueva.total).toContainText('250.000');

    await nueva.enviar();

    await expect(page).toHaveURL(/\/ordenes\/[0-9a-f-]{36}$/);
    await expect(page.getByTestId('aviso')).toHaveText('Orden creada.');
    await expect(new DetallePage(page).estado).toHaveText('CREADA');
  });

  test('consultar una orden desde el listado', { tag: ['@smoke'] }, async ({ page, request }) => {
    const orden = await crearOrdenPorApi(request);
    const listado = new ListadoPage(page);

    await listado.abrir();
    await expect(listado.fila(orden.id)).toBeVisible();
    await listado.abrirOrden(orden.id);

    await expect(page.getByRole('heading', { name: `Orden de ${orden.cliente}` })).toBeVisible();
    await expect(new DetallePage(page).estado).toHaveText('CREADA');
  });

  test('actualizar el estado hasta entregada', { tag: ['@RN-05', '@RN-06'] }, async ({ page, request }) => {
    const orden = await crearOrdenPorApi(request);
    const detalle = new DetallePage(page);
    await detalle.abrir(orden.id);

    // RN-05: una orden sin pagar no ofrece la acción de enviar.
    await expect(detalle.botonEstado('ENVIADA')).toHaveCount(0);

    for (const estado of ['PAGADA', 'ENVIADA', 'ENTREGADA'] as const) {
      await detalle.cambiarEstadoA(estado);
      await expect(detalle.estado).toHaveText(estado);
      await expect(page.getByTestId('aviso')).toContainText(estado.toLowerCase());
    }

    await expect(detalle.botonCancelar).toHaveCount(0);
    await expect(page.getByText('Esta orden ya no admite cambios de estado.')).toBeVisible();
  });

  test('cancelar una orden creada', { tag: ['@RN-04'] }, async ({ page, request }) => {
    const orden = await crearOrdenPorApi(request);
    const detalle = new DetallePage(page);
    await detalle.abrir(orden.id);

    await detalle.cancelar();

    await expect(page.getByTestId('aviso')).toHaveText('Orden cancelada.');
    await expect(detalle.estado).toHaveText('CANCELADA');
    await expect(detalle.botonCancelar).toHaveCount(0);
  });

  test('una orden entregada no ofrece cancelar', { tag: ['@RN-04'] }, async ({ page, request }) => {
    const orden = await crearOrdenPorApi(request);
    await llevarA(request, orden.id, 'PAGADA', 'ENVIADA', 'ENTREGADA');
    const detalle = new DetallePage(page);

    await detalle.abrir(orden.id);

    await expect(detalle.estado).toHaveText('ENTREGADA');
    await expect(detalle.botonCancelar).toHaveCount(0);
  });

  test('mostrar el error de la API junto al campo inválido', { tag: ['@RN-02'] }, async ({ page }) => {
    const nueva = new NuevaOrdenPage(page);
    await nueva.abrir();
    await nueva.llenar('Ana', [{ id: 'P001', cantidad: 0, valorUnitario: 1000 }]);

    await nueva.enviar();

    await expect(page.getByText('Debe ser mayor que 0.')).toBeVisible();
    await expect(page.getByTestId('input-cantidad-0')).toHaveAttribute('aria-invalid', 'true');
    await expect(page).toHaveURL(/\/ordenes\/nueva$/);
  });
});
```
