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
