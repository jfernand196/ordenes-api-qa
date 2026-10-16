Feature: Crear órdenes de compra

  Background:
    * url baseUrl

  @smoke @RN-03
  Scenario: Crear una orden válida
    Given path 'orders'
    And request { cliente: 'Juan Pérez', productos: [{ id: 'P001', cantidad: 2, valorUnitario: 100000 }] }
    When method post
    Then status 201
    And match response ==
      """
      {
        id: '#uuid',
        cliente: 'Juan Pérez',
        productos: [{ id: 'P001', cantidad: 2, valorUnitario: 100000 }],
        total: 200000,
        estado: 'CREADA',
        transicionesPermitidas: ['CANCELADA', 'PAGADA']
      }
      """
    And match karate.response.header('Location') == '/orders/' + response.id

  # Justificación: RN-03 exige que el total lo calcule el sistema. Aceptar un total
  # enviado por el cliente sería un riesgo de manipulación de precios.
  @RN-03
  Scenario: Rechazar una orden que trae el total desde el cliente
    Given path 'orders'
    And request { cliente: 'Ana', productos: [{ id: 'P001', cantidad: 1, valorUnitario: 1000 }], total: 1 }
    When method post
    Then status 422
    And match response.errores contains { campo: 'total', mensaje: 'Campo no permitido.' }

  # Justificación: RN-01 y RN-02 son la primera barrera de calidad de datos; se
  # verifican también contra la API desplegada, no solo en pruebas unitarias.
  @RN-01 @RN-02
  Scenario Outline: Rechazar una orden inválida: <caso>
    Given path 'orders'
    And request <payload>
    When method post
    Then status 422
    And match karate.response.header('Content-Type') contains 'application/problem+json'
    And match response.codigo == 'VALIDACION'
    And match response.errores[0].campo == '<campo>'

    Examples:
      | caso              | campo                | payload                                                                          |
      | sin productos     | productos            | { cliente: 'Ana', productos: [] }                                                |
      | cantidad cero     | productos.0.cantidad | { cliente: 'Ana', productos: [{ id: 'P1', cantidad: 0, valorUnitario: 1000 }] }  |
      | cantidad negativa | productos.0.cantidad | { cliente: 'Ana', productos: [{ id: 'P1', cantidad: -1, valorUnitario: 1000 }] } |
      | sin cliente       | cliente              | { productos: [{ id: 'P1', cantidad: 1, valorUnitario: 1000 }] }                  |
