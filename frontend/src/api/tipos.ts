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
