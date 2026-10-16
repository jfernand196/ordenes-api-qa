import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ESTADOS, type Estado } from '../api/tipos';
import { EstadoBadge } from '../componentes/EstadoBadge';
import { MensajeError } from '../componentes/MensajeError';
import { formatoMoneda } from '../formato';
import { useOrdenes } from '../hooks/useOrdenes';

export function ListadoOrdenes() {
  const [filtro, setFiltro] = useState<Estado | ''>('');
  const carga = useOrdenes(filtro || undefined);

  return (
    <main>
      <header className="barra">
        <h1>Órdenes de compra</h1>
        <Link to="/ordenes/nueva" className="boton primario" data-testid="btn-nueva-orden">
          Nueva orden
        </Link>
      </header>

      <label className="etiqueta" style={{ maxWidth: 240 }}>
        Filtrar por estado
        <select data-testid="filtro-estado" value={filtro} onChange={(e) => setFiltro(e.target.value as Estado | '')}>
          <option value="">Todos</option>
          {ESTADOS.map((e) => (
            <option key={e} value={e}>{e}</option>
          ))}
        </select>
      </label>

      {carga.tipo === 'cargando' && <p role="status">Cargando órdenes…</p>}
      {carga.tipo === 'error' && <MensajeError error={carga.error} />}
      {carga.tipo === 'ok' && carga.datos.length === 0 && (
        <p className="vacio">
          {filtro
            ? `No hay órdenes en estado ${filtro}.`
            : 'Todavía no hay órdenes. Crea la primera con «Nueva orden».'}
        </p>
      )}
      {carga.tipo === 'ok' && carga.datos.length > 0 && (
        <div className="tabla">
          <table>
            <thead>
              <tr>
                <th>Cliente</th>
                <th className="num">Productos</th>
                <th className="num">Total</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {carga.datos.map((o) => (
                <tr key={o.id} data-testid={`fila-orden-${o.id}`}>
                  <td><Link to={`/ordenes/${o.id}`}>{o.cliente}</Link></td>
                  <td className="num">{o.productos.length}</td>
                  <td className="num">{formatoMoneda(o.total)}</td>
                  <td><EstadoBadge estado={o.estado} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
