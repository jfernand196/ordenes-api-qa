Feature: Transiciones de estado de una orden

  Background:
    * url baseUrl
    * def creada = call read(crearOrden)
    * def ordenId = creada.ordenId

  @RN-05
  Scenario: Intentar enviar una orden no pagada
    Given path 'orders', ordenId, 'status'
    And request { estado: 'ENVIADA' }
    When method patch
    Then status 400
    And match karate.response.header('Content-Type') contains 'application/problem+json'
    And match response.codigo == 'RN-05'
    And match response.detail == 'La orden no puede enviarse si no ha sido pagada.'

  @RN-04
  Scenario: Intentar cancelar una orden entregada
    * call read(cambiarEstado) { id: '#(ordenId)', estado: 'PAGADA' }
    * call read(cambiarEstado) { id: '#(ordenId)', estado: 'ENVIADA' }
    * call read(cambiarEstado) { id: '#(ordenId)', estado: 'ENTREGADA' }
    Given path 'orders', ordenId
    When method delete
    Then status 409
    And match response.codigo == 'RN-04'

  # Justificación: es el camino feliz de mayor valor de negocio; si se rompe,
  # ninguna orden llega al cliente.
  @smoke @RN-05 @RN-06
  Scenario: Ciclo de vida completo hasta entregada
    * call read(cambiarEstado) { id: '#(ordenId)', estado: 'PAGADA' }
    * call read(cambiarEstado) { id: '#(ordenId)', estado: 'ENVIADA' }
    Given path 'orders', ordenId, 'status'
    And request { estado: 'ENTREGADA' }
    When method patch
    Then status 200
    And match response.estado == 'ENTREGADA'
    And match response.transicionesPermitidas == []

  # Justificación: saltarse estados (CREADA a ENTREGADA) es la transición inválida
  # de mayor impacto: entregaría mercancía sin pago ni envío registrados.
  @RN-06
  Scenario: Rechazar una transición que se salta estados
    Given path 'orders', ordenId, 'status'
    And request { estado: 'ENTREGADA' }
    When method patch
    Then status 409
    And match response.codigo == 'RN-06'

  # Justificación: supuesto documentado. RN-04 solo prohíbe cancelar una orden
  # ENTREGADA, así que una ENVIADA sí puede cancelarse.
  @RN-04
  Scenario: Cancelar una orden enviada
    * call read(cambiarEstado) { id: '#(ordenId)', estado: 'PAGADA' }
    * call read(cambiarEstado) { id: '#(ordenId)', estado: 'ENVIADA' }
    Given path 'orders', ordenId
    When method delete
    Then status 200
    And match response.estado == 'CANCELADA'

  Scenario: Cancelar una orden creada
    Given path 'orders', ordenId
    When method delete
    Then status 200
    And match response.estado == 'CANCELADA'

  # Justificación: ENTREGADA es terminal. Reactivarla o moverla de nuevo a otro estado
  # alteraría una orden cerrada (riesgo crítico según transiciones_sin_aceptacion del MCP).
  @RN-04
  Scenario Outline: Rechazar cambios sobre una orden entregada: ENTREGADA a <destino>
    * call read(cambiarEstado) { id: '#(ordenId)', estado: 'PAGADA' }
    * call read(cambiarEstado) { id: '#(ordenId)', estado: 'ENVIADA' }
    * call read(cambiarEstado) { id: '#(ordenId)', estado: 'ENTREGADA' }
    Given path 'orders', ordenId, 'status'
    And request { estado: '<destino>' }
    When method patch
    Then status 409
    And match karate.response.header('Content-Type') contains 'application/problem+json'
    And match response.codigo == 'RN-04'
    Given path 'orders', ordenId
    When method get
    Then status 200
    And match response.estado == 'ENTREGADA'

    Examples:
      | destino |
      | CREADA  |
      | PAGADA  |
      | ENVIADA |

  # Justificación: CANCELADA es terminal. Ningún cambio posterior debe revivir la orden,
  # ni siquiera hacia ENTREGADA, que despacharía mercancía de una orden anulada.
  @RN-04
  Scenario Outline: Rechazar cambios sobre una orden cancelada: CANCELADA a <destino>
    Given path 'orders', ordenId
    When method delete
    Then status 200
    Given path 'orders', ordenId, 'status'
    And request { estado: '<destino>' }
    When method patch
    Then status 409
    And match karate.response.header('Content-Type') contains 'application/problem+json'
    And match response.codigo == 'RN-04'
    Given path 'orders', ordenId
    When method get
    Then status 200
    And match response.estado == 'CANCELADA'

    Examples:
      | destino   |
      | CREADA    |
      | PAGADA    |
      | ENVIADA   |
      | ENTREGADA |
