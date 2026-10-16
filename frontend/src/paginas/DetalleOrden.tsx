import { useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { aApiError, type ApiError, ordenesApi } from '../api/ordenes';
import type { Estado, Orden } from '../api/tipos';
import { EstadoBadge } from '../componentes/EstadoBadge';
import { MensajeError } from '../componentes/MensajeError';
import { formatoMoneda } from '../formato';
import { useOrden } from '../hooks/useOrden';

const ACCIONES: Partial<Record<Estado, { boton: string; aviso: string }>> = {
  PAGADA: { boton: 'Marcar como pagada', aviso: 'Orden marcada como pagada.' },
  ENVIADA: { boton: 'Marcar como enviada', aviso: 'Orden marcada como enviada.' },
  ENTREGADA: { boton: 'Marcar como entregada', aviso: 'Orden marcada como entregada.' },
};

function avisoInicial(state: unknown): string | null {
  if (state && typeof state === 'object' && 'aviso' in state && typeof state.aviso === 'string') {
    return state.aviso;
  }
  return null;
}

export function DetalleOrden() {
  const { id = '' } = useParams();
  const location = useLocation();
  const { carga, setOrden } = useOrden(id);
  const [errorAccion, setErrorAccion] = useState<ApiError | null>(null);
  const [aviso, setAviso] = useState<string | null>(() => avisoInicial(location.state));
  const [ocupado, setOcupado] = useState(false);

  if (carga.tipo === 'cargando') return <main><p role="status">Cargando orden…</p></main>;
  if (carga.tipo === 'error') {
    return (
      <main>
        <Link to="/">Volver al listado</Link>
        <MensajeError error={carga.error} />
      </main>
    );
  }

  const orden = carga.datos;
  // La API es la fuente de verdad de la máquina de estados.
  const avances = orden.transicionesPermitidas.filter((e) => e !== 'CANCELADA');
  const puedeCancelar = orden.transicionesPermitidas.includes('CANCELADA');

  async function ejecutar(accion: () => Promise<Orden>, mensajeExito: string) {
    setOcupado(true);
    setErrorAccion(null);
    setAviso(null);
    try {
      setOrden(await accion());
      setAviso(mensajeExito);
    } catch (e) {
      setErrorAccion(aApiError(e));
    } finally {
      setOcupado(false);
    }
  }

  return (
    <main>
      <Link to="/">Volver al listado</Link>
      <header className="barra">
        <h1>Orden de {orden.cliente}</h1>
        <EstadoBadge estado={orden.estado} grande testId="estado-orden" />
      </header>

      {aviso && <p role="status" className="aviso" data-testid="aviso">{aviso}</p>}
      {errorAccion && <MensajeError error={errorAccion} />}

      <div className="tabla">
        <table>
          <thead>
            <tr>
              <th>Producto</th>
              <th className="num">Cantidad</th>
              <th className="num">Valor unitario</th>
              <th className="num">Subtotal</th>
            </tr>
          </thead>
          <tbody>
            {orden.productos.map((p) => (
              <tr key={p.id}>
                <td>{p.id}</td>
                <td className="num">{p.cantidad}</td>
                <td className="num">{formatoMoneda(p.valorUnitario)}</td>
                <td className="num">{formatoMoneda(p.cantidad * p.valorUnitario)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="total">
        <span>Total</span>
        <strong>{formatoMoneda(orden.total)}</strong>
      </div>

      {orden.transicionesPermitidas.length === 0 ? (
        <p className="nota">Esta orden ya no admite cambios de estado.</p>
      ) : (
        <div className="acciones">
          {avances.map((estado) => (
            <button key={estado} className="primario" data-testid={`btn-estado-${estado}`} disabled={ocupado}
              onClick={() => ejecutar(() => ordenesApi.cambiarEstado(orden.id, estado), ACCIONES[estado]?.aviso ?? 'Estado actualizado.')}>
              {ACCIONES[estado]?.boton ?? estado}
            </button>
          ))}
          {puedeCancelar && (
            <button className="peligro" data-testid="btn-cancelar-orden" disabled={ocupado}
              onClick={() => {
                if (window.confirm('¿Cancelar esta orden? Esta acción no se puede deshacer.')) {
                  ejecutar(() => ordenesApi.cancelar(orden.id), 'Orden cancelada.');
                }
              }}>
              Cancelar orden
            </button>
          )}
        </div>
      )}
    </main>
  );
}
