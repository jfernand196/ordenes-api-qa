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
