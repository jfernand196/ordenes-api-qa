import type { Estado, NuevaOrden, Orden, Problema } from './tipos';

const BASE = '/api';

export class ApiError extends Error {
  readonly status: number;
  readonly problema: Problema;

  constructor(status: number, problema: Problema) {
    super(problema.detail ?? problema.title);
    this.name = 'ApiError';
    this.status = status;
    this.problema = problema;
  }
}

export function aApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;
  return new ApiError(0, {
    title: 'No se pudo conectar con la API. Verifica que esté en ejecución y recarga la página.',
    status: 0,
  });
}

async function solicitar<T>(ruta: string, init?: RequestInit): Promise<T> {
  const respuesta = await fetch(`${BASE}${ruta}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  const cuerpo = await respuesta.json().catch(() => null);
  if (!respuesta.ok) {
    throw new ApiError(respuesta.status, cuerpo ?? { title: respuesta.statusText, status: respuesta.status });
  }
  return cuerpo as T;
}

export const ordenesApi = {
  listar: (estado?: Estado) => solicitar<Orden[]>(estado ? `/orders?estado=${estado}` : '/orders'),
  obtener: (id: string) => solicitar<Orden>(`/orders/${id}`),
  crear: (datos: NuevaOrden) =>
    solicitar<Orden>('/orders', { method: 'POST', body: JSON.stringify(datos) }),
  cambiarEstado: (id: string, estado: Estado) =>
    solicitar<Orden>(`/orders/${id}/status`, { method: 'PATCH', body: JSON.stringify({ estado }) }),
  cancelar: (id: string) => solicitar<Orden>(`/orders/${id}`, { method: 'DELETE' }),
};
