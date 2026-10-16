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
