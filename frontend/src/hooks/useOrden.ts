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

  // Reemplaza la orden tras una acción sin volver a pedirla a la API.
  const setOrden = (orden: Orden) => setCarga({ tipo: 'ok', datos: orden });
  return { carga, setOrden };
}
