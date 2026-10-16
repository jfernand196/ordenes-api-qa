import type { Locator, Page } from '@playwright/test';

export interface ProductoFormulario {
  id: string;
  cantidad: number;
  valorUnitario: number;
}

export class NuevaOrdenPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async abrir() {
    await this.page.goto('/ordenes/nueva');
  }

  get total(): Locator {
    return this.page.getByTestId('total-orden');
  }

  get mensajeError(): Locator {
    return this.page.getByTestId('mensaje-error');
  }

  async llenar(cliente: string, productos: ProductoFormulario[]) {
    await this.page.getByTestId('input-cliente').fill(cliente);
    for (const [i, p] of productos.entries()) {
      if (i > 0) await this.page.getByTestId('btn-agregar-producto').click();
      await this.page.getByTestId(`input-producto-id-${i}`).fill(p.id);
      await this.page.getByTestId(`input-cantidad-${i}`).fill(String(p.cantidad));
      await this.page.getByTestId(`input-valor-${i}`).fill(String(p.valorUnitario));
    }
  }

  async enviar() {
    await this.page.getByTestId('btn-crear-orden').click();
  }
}
