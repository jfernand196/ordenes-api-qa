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
