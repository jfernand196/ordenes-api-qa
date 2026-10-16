import type { ApiError } from './ordenes';

/** Estado de una carga asíncrona: imposible estar "cargando y con error" a la vez. */
export type Carga<T> =
  | { tipo: 'cargando' }
  | { tipo: 'ok'; datos: T }
  | { tipo: 'error'; error: ApiError };
