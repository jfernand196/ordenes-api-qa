Feature: Consultar y listar órdenes

  Background:
    * url baseUrl
    * def creada = call read(crearOrden)
    * def ordenId = creada.ordenId

  @smoke
  Scenario: Consultar una orden existente
    Given path 'orders', ordenId
    When method get
    Then status 200
    And match response.id == ordenId
    And match response.estado == 'CREADA'

  # Justificación: un id inexistente es un error frecuente de los consumidores;
  # debe responder 404 con Problem Details y no un 500.
  Scenario: Consultar una orden inexistente
    Given path 'orders', '00000000-0000-0000-0000-000000000000'
    When method get
    Then status 404
    And match response.codigo == 'NO_ENCONTRADA'

  Scenario: Listar órdenes filtradas por estado
    * call read(cambiarEstado) { id: '#(ordenId)', estado: 'PAGADA' }
    Given path 'orders'
    And param estado = 'PAGADA'
    When method get
    Then status 200
    And match each response contains { estado: 'PAGADA' }
    And match response[*].id contains ordenId
