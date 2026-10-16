@ignore
Feature: Helper para crear una orden válida

  Scenario:
    * def cliente = karate.get('cliente', 'Cliente Karate')
    Given url baseUrl
    And path 'orders'
    And request { cliente: '#(cliente)', productos: [{ id: 'P001', cantidad: 1, valorUnitario: 50000 }] }
    When method post
    Then status 201
    * def ordenId = response.id
