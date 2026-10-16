@ignore
Feature: Helper para cambiar el estado de una orden (espera éxito)

  Scenario:
    Given url baseUrl
    And path 'orders', id, 'status'
    And request { estado: '#(estado)' }
    When method patch
    Then status 200
