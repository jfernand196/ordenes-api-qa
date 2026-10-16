import type { ApiError } from '../api/ordenes';

export function MensajeError({ error, conDetalle = true }: { error: ApiError; conDetalle?: boolean }) {
  return (
    <div role="alert" data-testid="mensaje-error" className="error">
      <p>{error.message}</p>
      {conDetalle && error.problema.errores && (
        <ul>
          {error.problema.errores.map((e) => (
            <li key={e.campo}>{e.mensaje}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

/** Mensaje de error de la API para un campo concreto, por ejemplo "productos.0.cantidad". */
export function errorDeCampo(error: ApiError | null, campo: string): string | undefined {
  return error?.problema.errores?.find((e) => e.campo === campo)?.mensaje;
}
