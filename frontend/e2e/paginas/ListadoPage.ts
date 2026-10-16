import type { Locator, Page } from '@playwright/test';

export class ListadoPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async abrir() {
    await this.page.goto('/');
  }

  fila(id: string): Locator {
    return this.page.getByTestId(`fila-orden-${id}`);
  }

  async filtrarPor(estado: string) {
    await this.page.getByTestId('filtro-estado').selectOption(estado);
  }

  async abrirOrden(id: string) {
    await this.fila(id).getByRole('link').click();
  }

  async irANuevaOrden() {
    await this.page.getByTestId('btn-nueva-orden').click();
  }
}
