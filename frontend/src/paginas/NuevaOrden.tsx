import { type FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { aApiError, ApiError, ordenesApi } from '../api/ordenes';
import { Campo } from '../componentes/Campo';
import { MensajeError, errorDeCampo } from '../componentes/MensajeError';
import { formatoMoneda } from '../formato';

// Cada fila lleva una clave estable: usar el índice como key rompe los inputs al quitar filas.
type Fila = { clave: number; id: string; cantidad: string; valorUnitario: string };
let siguienteClave = 0;
const filaVacia = (): Fila => ({ clave: siguienteClave++, id: '', cantidad: '1', valorUnitario: '' });

export function NuevaOrden() {
  const navegar = useNavigate();
  const [cliente, setCliente] = useState('');
  const [filas, setFilas] = useState<Fila[]>(() => [filaVacia()]);
  const [error, setError] = useState<ApiError | null>(null);
  const [enviando, setEnviando] = useState(false);

  // Derivado: se calcula en cada render, no se guarda en estado. Solo visual (RN-03).
  const total = filas.reduce(
    (suma, f) => suma + (Number(f.cantidad) || 0) * (Number(f.valorUnitario) || 0),
    0,
  );

  // Al editar un campo, su error deja de mostrarse: ya no describe lo que hay en pantalla.
  const limpiarErrorDe = (campo: string) =>
    setError((e) =>
      e?.problema.errores
        ? new ApiError(e.status, {
            ...e.problema,
            errores: e.problema.errores.filter((x) => x.campo !== campo),
          })
        : e,
    );

  const actualizar = (clave: number, campo: 'id' | 'cantidad' | 'valorUnitario', valor: string) => {
    const i = filas.findIndex((f) => f.clave === clave);
    setFilas((fs) => fs.map((f) => (f.clave === clave ? { ...f, [campo]: valor } : f)));
    limpiarErrorDe(`productos.${i}.${campo}`);
  };

  async function guardar(evento: FormEvent) {
    evento.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      const orden = await ordenesApi.crear({
        cliente,
        productos: filas.map((f) => ({
          id: f.id,
          cantidad: Number(f.cantidad),
          valorUnitario: Number(f.valorUnitario),
        })),
      });
      navegar(`/ordenes/${orden.id}`, { state: { aviso: 'Orden creada.' } });
    } catch (e) {
      setError(aApiError(e));
      setEnviando(false);
    }
  }

  return (
    <main>
      <Link to="/">Volver al listado</Link>
      <h1>Nueva orden</h1>

      {error && error.problema.errores?.length !== 0 && <MensajeError error={error} conDetalle={false} />}

      <form onSubmit={guardar} noValidate>
        <Campo etiqueta="Cliente" valor={cliente} onCambio={(v) => {
            setCliente(v);
            limpiarErrorDe('cliente');
          }}
          error={errorDeCampo(error, 'cliente')} testId="input-cliente" />

        {filas.map((f, i) => (
          <fieldset key={f.clave}>
            <legend>Producto {i + 1}</legend>
            <div className="fila-producto">
              <Campo etiqueta="Código" valor={f.id} onCambio={(v) => actualizar(f.clave, 'id', v)}
                error={errorDeCampo(error, `productos.${i}.id`)} testId={`input-producto-id-${i}`} />
              <Campo etiqueta="Cantidad" numerico valor={f.cantidad} onCambio={(v) => actualizar(f.clave, 'cantidad', v)}
                error={errorDeCampo(error, `productos.${i}.cantidad`)} testId={`input-cantidad-${i}`} />
              <Campo etiqueta="Valor unitario" numerico valor={f.valorUnitario}
                onCambio={(v) => actualizar(f.clave, 'valorUnitario', v)}
                error={errorDeCampo(error, `productos.${i}.valorUnitario`)} testId={`input-valor-${i}`} />
              {filas.length > 1 && (
                <button type="button" onClick={() => {
                  setFilas((fs) => fs.filter((x) => x.clave !== f.clave));
                  setError(null); // los indices de los errores dejan de corresponder
                }}>
                  Quitar
                </button>
              )}
            </div>
          </fieldset>
        ))}

        <div>
          <button type="button" data-testid="btn-agregar-producto" onClick={() => setFilas((fs) => [...fs, filaVacia()])}>
            Agregar producto
          </button>
        </div>

        <div className="total">
          <span>Total <span className="nota">(calculado automáticamente)</span></span>
          <strong data-testid="total-orden">{formatoMoneda(total)}</strong>
        </div>

        <div className="acciones">
          <button type="submit" className="primario" data-testid="btn-crear-orden" disabled={enviando}>
            {enviando ? 'Creando…' : 'Crear orden'}
          </button>
        </div>
      </form>
    </main>
  );
}
