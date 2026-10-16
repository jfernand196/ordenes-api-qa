import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { ApiError, ordenesApi } from '../api/ordenes';
import { NuevaOrden } from './NuevaOrden';

vi.mock('../api/ordenes', async (importOriginal) => {
  const real = await importOriginal<typeof import('../api/ordenes')>();
  return { ...real, ordenesApi: { crear: vi.fn() } };
});

function renderizar() {
  render(
    <MemoryRouter>
      <NuevaOrden />
    </MemoryRouter>,
  );
}

// Intl separa miles con un espacio especial según el entorno; se comparan solo los dígitos.
const digitos = (texto: string | null) => (texto ?? '').replace(/\D/g, '');

describe('NuevaOrden', () => {
  it('calcula el total visual al escribir cantidades y valores', async () => {
    const usuario = userEvent.setup();
    renderizar();
    await usuario.clear(screen.getByTestId('input-cantidad-0'));
    await usuario.type(screen.getByTestId('input-cantidad-0'), '3');
    await usuario.type(screen.getByTestId('input-valor-0'), '1500');
    expect(digitos(screen.getByTestId('total-orden').textContent)).toBe('4500');
  });

  it('agrega y quita productos conservando los datos de las demás filas', async () => {
    const usuario = userEvent.setup();
    renderizar();
    await usuario.type(screen.getByTestId('input-producto-id-0'), 'A');
    await usuario.click(screen.getByTestId('btn-agregar-producto'));
    await usuario.type(screen.getByTestId('input-producto-id-1'), 'B');

    await usuario.click(screen.getAllByRole('button', { name: 'Quitar' })[0]);

    expect(screen.getByTestId('input-producto-id-0')).toHaveValue('B');
    expect(screen.queryByTestId('input-producto-id-1')).not.toBeInTheDocument();
  });

  it('muestra junto al campo el error de validación que devuelve la API', async () => {
    vi.mocked(ordenesApi.crear).mockRejectedValue(
      new ApiError(422, {
        title: 'Solicitud inválida',
        status: 422,
        detail: 'El cuerpo o los parámetros no son válidos.',
        errores: [{ campo: 'productos.0.cantidad', mensaje: 'Debe ser mayor que 0.' }],
      }),
    );
    const usuario = userEvent.setup();
    renderizar();
    await usuario.click(screen.getByTestId('btn-crear-orden'));

    expect(await screen.findByText('Debe ser mayor que 0.')).toBeInTheDocument();
    expect(screen.getByTestId('input-cantidad-0')).toHaveAttribute('aria-invalid', 'true');
  });

  it('oculta el error de un campo cuando el usuario lo corrige', async () => {
    vi.mocked(ordenesApi.crear).mockRejectedValue(
      new ApiError(422, {
        title: 'Solicitud invalida',
        status: 422,
        errores: [{ campo: 'productos.0.cantidad', mensaje: 'Debe ser mayor que 0.' }],
      }),
    );
    const usuario = userEvent.setup();
    renderizar();
    await usuario.click(screen.getByTestId('btn-crear-orden'));
    expect(await screen.findByText('Debe ser mayor que 0.')).toBeInTheDocument();

    await usuario.type(screen.getByTestId('input-cantidad-0'), '5');

    expect(screen.queryByText('Debe ser mayor que 0.')).not.toBeInTheDocument();
    expect(screen.getByTestId('input-cantidad-0')).not.toHaveAttribute('aria-invalid');
    expect(screen.queryByTestId('mensaje-error')).not.toBeInTheDocument();
  });
});
