import type { Locator, Page } from '@playwright/test';
import type { Estado } from '../datos';

export class DetallePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async abrir(id: string) {
    await this.page.goto(`/ordenes/${id}`);
  }

  get estado(): Locator {
    return this.page.getByTestId('estado-orden');
  }

  get botonCancelar(): Locator {
    return this.page.getByTestId('btn-cancelar-orden');
  }

  botonEstado(estado: Estado): Locator {
    return this.page.getByTestId(`btn-estado-${estado}`);
  }

  async cambiarEstadoA(estado: Estado) {
    await this.botonEstado(estado).click();
  }

  async cancelar() {
    this.page.once('dialog', (dialogo) => dialogo.accept());
    await this.botonCancelar.click();
  }
}
