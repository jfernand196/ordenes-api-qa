# Plantillas del frontend

El template `react-ts` de Vite activa `verbatimModuleSyntax` y, en versiones recientes, `erasableSyntaxOnly`. Por eso los tipos se importan con `import type` y las clases no usan propiedades en el constructor (`constructor(public x)`).

Contenido:
1. vite.config.ts y setup de pruebas
2. API: tipos y cliente
3. Utilidades, hooks y componentes
4. Páginas
5. App.tsx
6. Prueba de ejemplo
7. nginx.conf, Dockerfile y .dockerignore

---

## 1. Configuración

### vite.config.ts
```ts
/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        rewrite: (ruta) => ruta.replace(/^\/api/, ''),
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    include: ['src/**/*.test.{ts,tsx}'], // evita que Vitest tome las pruebas de e2e/
  },
});
```

### src/test/setup.ts
```ts
import '@testing-library/jest-dom/vitest';
```

---

## 2. API

### src/api/tipos.ts
```ts
export const ESTADOS = ['CREADA', 'PAGADA', 'ENVIADA', 'ENTREGADA', 'CANCELADA'] as const;
export type Estado = (typeof ESTADOS)[number];

export interface Producto {
  id: string;
  cantidad: number;
  valorUnitario: number;
}

export interface Orden {
  id: string;
  cliente: string;
  productos: Producto[];
  total: number;
  estado: Estado;
  transicionesPermitidas: Estado[];
}

export interface NuevaOrden {
  cliente: string;
  productos: Producto[];
}

export interface Problema {
  title: string;
  status: number;
  detail?: string;
  codigo?: string;
  errores?: { campo: string; mensaje: string }[];
}
```

### src/api/ordenes.ts
```ts
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
  return new ApiError(0, { title: 'No se pudo conectar con la API', status: 0 });
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
```

---

## 3. Utilidades, hooks y componentes

### src/formato.ts
```ts
const moneda = new Intl.NumberFormat('es-CO', {
  style: 'currency',
  currency: 'COP',
  maximumFractionDigits: 0,
});

export const formatoMoneda = (valor: number) => moneda.format(valor);
```

### src/api/carga.ts
```ts
import type { ApiError } from './ordenes';

/** Estado de una carga asíncrona: imposible estar "cargando y con error" a la vez. */
export type Carga<T> =
  | { tipo: 'cargando' }
  | { tipo: 'ok'; datos: T }
  | { tipo: 'error'; error: ApiError };
```

### src/hooks/useOrdenes.ts
```ts
import { useEffect, useState } from 'react';
import type { Carga } from '../api/carga';
import { aApiError, ordenesApi } from '../api/ordenes';
import type { Estado, Orden } from '../api/tipos';

export function useOrdenes(filtro?: Estado): Carga<Orden[]> {
  const [carga, setCarga] = useState<Carga<Orden[]>>({ tipo: 'cargando' });

  useEffect(() => {
    let vigente = true; // evita que una respuesta vieja pise a la del filtro actual
    setCarga({ tipo: 'cargando' });
    ordenesApi
      .listar(filtro)
      .then((datos) => {
        if (vigente) setCarga({ tipo: 'ok', datos });
      })
      .catch((e) => {
        if (vigente) setCarga({ tipo: 'error', error: aApiError(e) });
      });
    return () => {
      vigente = false;
    };
  }, [filtro]);

  return carga;
}
```

### src/hooks/useOrden.ts
```ts
import { useEffect, useState } from 'react';
import type { Carga } from '../api/carga';
import { aApiError, ordenesApi } from '../api/ordenes';
import type { Orden } from '../api/tipos';

export function useOrden(id: string) {
  const [carga, setCarga] = useState<Carga<Orden>>({ tipo: 'cargando' });

  useEffect(() => {
    let vigente = true;
    setCarga({ tipo: 'cargando' });
    ordenesApi
      .obtener(id)
      .then((datos) => {
        if (vigente) setCarga({ tipo: 'ok', datos });
      })
      .catch((e) => {
        if (vigente) setCarga({ tipo: 'error', error: aApiError(e) });
      });
    return () => {
      vigente = false;
    };
  }, [id]);

  // setOrden permite reemplazar la orden tras una acción sin volver a pedirla.
  const setOrden = (orden: Orden) => setCarga({ tipo: 'ok', datos: orden });
  return { carga, setOrden };
}
```

### src/componentes/MensajeError.tsx
```tsx
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
```

### src/componentes/EstadoBadge.tsx
```tsx
import type { Estado } from '../api/tipos';

export function EstadoBadge({ estado, grande = false, testId }: { estado: Estado; grande?: boolean; testId?: string }) {
  const clases = `estado estado-${estado.toLowerCase()}${grande ? ' estado-grande' : ''}`;
  return (
    <span className={clases} data-testid={testId}>
      {estado}
    </span>
  );
}
```

### src/componentes/Campo.tsx
```tsx
import { useId } from 'react';

interface CampoProps {
  etiqueta: string;
  valor: string;
  onCambio: (valor: string) => void;
  error?: string;
  numerico?: boolean;
  testId?: string;
}

/** Input con label visible y error accesible (aria-invalid + aria-describedby). */
export function Campo({ etiqueta, valor, onCambio, error, numerico = false, testId }: CampoProps) {
  const id = useId();
  const idError = `${id}-error`;
  return (
    <label htmlFor={id}>
      {etiqueta}
      <input
        id={id}
        value={valor}
        onChange={(e) => onCambio(e.target.value)}
        inputMode={numerico ? 'numeric' : undefined}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? idError : undefined}
        data-testid={testId}
      />
      {error && (
        <span id={idError} className="campo-error">
          {error}
        </span>
      )}
    </label>
  );
}
```

---

## 4. Páginas

### src/paginas/ListadoOrdenes.tsx
```tsx
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
```

`e.target.value as Estado | ''` es seguro: las opciones del select salen de `ESTADOS`.

### src/paginas/NuevaOrden.tsx
```tsx
import { type FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { aApiError, type ApiError, ordenesApi } from '../api/ordenes';
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

  const actualizar = (clave: number, campo: 'id' | 'cantidad' | 'valorUnitario', valor: string) =>
    setFilas((fs) => fs.map((f) => (f.clave === clave ? { ...f, [campo]: valor } : f)));

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

      {error && <MensajeError error={error} conDetalle={false} />}

      <form onSubmit={guardar} noValidate>
        <Campo etiqueta="Cliente" valor={cliente} onCambio={setCliente}
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
                <button type="button" onClick={() => setFilas((fs) => fs.filter((x) => x.clave !== f.clave))}>
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
```

El formulario usa `noValidate` a propósito: las reglas las valida la API y la UI muestra cada error junto a su campo. Así el frontend no duplica reglas del backend. Los mensajes llegan en español desde la API.

### src/paginas/DetalleOrden.tsx
```tsx
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
```

La clave `p.id` de la tabla de productos es estable: los productos de una orden ya creada no cambian.

---

## 5. src/App.tsx

```tsx
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { DetalleOrden } from './paginas/DetalleOrden';
import { ListadoOrdenes } from './paginas/ListadoOrdenes';
import { NuevaOrden } from './paginas/NuevaOrden';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ListadoOrdenes />} />
        <Route path="/ordenes/nueva" element={<NuevaOrden />} />
        <Route path="/ordenes/:id" element={<DetalleOrden />} />
      </Routes>
    </BrowserRouter>
  );
}
```

### src/main.tsx
```tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './estilos.css'; // del skill ui-ux-experto (assets/estilos.css)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
```

El `!` aquí es la única excepción aceptada: `#root` existe siempre en `index.html`. Cambia también `<html lang="es">` y el `<title>` en `index.html`.

---

## 6. src/paginas/DetalleOrden.test.tsx

```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, ordenesApi } from '../api/ordenes';
import type { Orden } from '../api/tipos';
import { DetalleOrden } from './DetalleOrden';

vi.mock('../api/ordenes', async (importOriginal) => {
  const real = await importOriginal<typeof import('../api/ordenes')>();
  return {
    ...real,
    ordenesApi: { obtener: vi.fn(), cambiarEstado: vi.fn(), cancelar: vi.fn() },
  };
});

const creada: Orden = {
  id: 'abc',
  cliente: 'Ana',
  productos: [{ id: 'P1', cantidad: 2, valorUnitario: 1000 }],
  total: 2000,
  estado: 'CREADA',
  transicionesPermitidas: ['CANCELADA', 'PAGADA'],
};

function renderizar() {
  render(
    <MemoryRouter initialEntries={['/ordenes/abc']}>
      <Routes>
        <Route path="/ordenes/:id" element={<DetalleOrden />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('DetalleOrden', () => {
  beforeEach(() => {
    vi.mocked(ordenesApi.obtener).mockResolvedValue(creada);
  });

  it('muestra solo los botones de las transiciones permitidas', async () => {
    renderizar();
    expect(await screen.findByTestId('btn-estado-PAGADA')).toBeInTheDocument();
    expect(screen.queryByTestId('btn-estado-ENVIADA')).not.toBeInTheDocument();
    expect(screen.getByTestId('btn-cancelar-orden')).toBeInTheDocument();
  });

  it('actualiza el estado tras un cambio exitoso', async () => {
    vi.mocked(ordenesApi.cambiarEstado).mockResolvedValue({
      ...creada,
      estado: 'PAGADA',
      transicionesPermitidas: ['CANCELADA', 'ENVIADA'],
    });
    renderizar();
    await userEvent.click(await screen.findByTestId('btn-estado-PAGADA'));
    expect(await screen.findByTestId('estado-orden')).toHaveTextContent('PAGADA');
    expect(screen.getByTestId('btn-estado-ENVIADA')).toBeInTheDocument();
  });

  it('muestra el error que devuelve la API', async () => {
    vi.mocked(ordenesApi.cambiarEstado).mockRejectedValue(
      new ApiError(409, { title: 'Transición inválida', status: 409, detail: 'Transición inválida de CREADA a PAGADA.' }),
    );
    renderizar();
    await userEvent.click(await screen.findByTestId('btn-estado-PAGADA'));
    expect(await screen.findByTestId('mensaje-error')).toHaveTextContent('Transición inválida');
  });
});
```

---

## 7. Docker

### nginx.conf
```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # /api/orders -> http://api:8080/orders (la barra final de proxy_pass quita el prefijo /api)
    location /api/ {
        proxy_pass http://api:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Request-ID $request_id;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Rutas de React Router
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### Dockerfile
```dockerfile
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --retries=5 CMD wget -qO- http://localhost/ >/dev/null || exit 1
```

### .dockerignore
```text
node_modules
dist
e2e
playwright-report
test-results
coverage
```
