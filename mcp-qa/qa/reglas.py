"""Reglas de negocio con su implementación y cuántas pruebas las verifican por nivel."""

from qa.trazabilidad import matriz

# Dónde vive cada regla. Una prueba exige que tenga exactamente las mismas reglas que el
# escáner de trazabilidad, así que no puede quedar desactualizado sin que se note.
IMPLEMENTACION = {
    "RN-01": "OrdenIn (min_length=1) en la API y Orden.__init__ en el dominio",
    "RN-02": "ProductoIn (gt=0) en la API y LineaProducto.__post_init__ en el dominio",
    "RN-03": "Propiedad Orden.total; OrdenIn rechaza un total enviado por el cliente",
    "RN-04": "ENTREGADA es estado terminal en TRANSICIONES (maquina_estados.py)",
    "RN-05": "validar_transicion: CREADA -> ENVIADA lanza PagoRequeridoError",
    "RN-06": "validar_transicion: cualquier destino fuera de TRANSICIONES",
}


def listar() -> list[dict[str, object]]:
    return [
        {
            "regla": fila.regla,
            "descripcion": fila.descripcion,
            "implementacion": IMPLEMENTACION[fila.regla],
            "pruebas": {
                "unitarias_e_integracion": len(fila.unitarias_e_integracion),
                "aceptacion_karate": len(fila.aceptacion_karate),
                "e2e_playwright": len(fila.e2e_playwright),
            },
            "estado": fila.estado,
        }
        for fila in matriz()
    ]
