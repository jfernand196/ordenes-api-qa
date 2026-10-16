# Plantillas de Karate

Contenido:
1. pom.xml
2. Runner JUnit 5
3. karate-config.js
4. Helpers
5. crear-orden.feature
6. consultar-orden.feature
7. transiciones.feature

---

## 1. acceptance-tests/pom.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.reto.ordenes</groupId>
    <artifactId>acceptance-tests</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <maven.compiler.release>17</maven.compiler.release>
        <karate.version>1.4.1</karate.version>
        <baseUrl>http://localhost:8080</baseUrl>
    </properties>

    <dependencies>
        <dependency>
            <groupId>io.karatelabs</groupId>
            <artifactId>karate-junit5</artifactId>
            <version>${karate.version}</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <testResources>
            <testResource>
                <directory>src/test/java</directory>
                <excludes>
                    <exclude>**/*.java</exclude>
                </excludes>
            </testResource>
        </testResources>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.2.5</version>
                <configuration>
                    <argLine>-Dfile.encoding=UTF-8</argLine>
                    <systemPropertyVariables>
                        <baseUrl>${baseUrl}</baseUrl>
                    </systemPropertyVariables>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

---

## 2. src/test/java/ordenes/OrdenesTest.java

```java
package ordenes;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.intuit.karate.Results;
import com.intuit.karate.Runner;
import org.junit.jupiter.api.Test;

class OrdenesTest {

    @Test
    void ejecutarEscenarios() {
        Results resultados = Runner.path("classpath:ordenes")
                .tags("~@ignore")
                .outputJunitXml(true)
                .parallel(4);
        assertEquals(0, resultados.getFailCount(), resultados.getErrorMessages());
    }
}
```

---

## 3. src/test/java/karate-config.js

```javascript
function fn() {
  var baseUrl = karate.properties['baseUrl'] || 'http://localhost:8080';
  karate.log('baseUrl =', baseUrl);
  karate.configure('connectTimeout', 5000);
  karate.configure('readTimeout', 10000);
  karate.configure('headers', { 'X-Request-ID': 'karate-' + java.util.UUID.randomUUID() });
  return {
    baseUrl: baseUrl,
    crearOrden: 'classpath:ordenes/helpers/crear-orden.feature',
    cambiarEstado: 'classpath:ordenes/helpers/cambiar-estado.feature'
  };
}
```

---

## 4. Helpers

### src/test/java/ordenes/helpers/crear-orden.feature
```gherkin
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
```

### src/test/java/ordenes/helpers/cambiar-estado.feature
```gherkin
@ignore
Feature: Helper para cambiar el estado de una orden (espera éxito)

  Scenario:
    Given url baseUrl
    And path 'orders', id, 'status'
    And request { estado: '#(estado)' }
    When method patch
    Then status 200
```

---

## 5. src/test/java/ordenes/crear-orden.feature

```gherkin
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

  # Justificación: RN-03 exige que el total lo calcule el sistema; un total enviado
  # por el cliente es un riesgo de manipulación de precios, por eso se rechaza.
  @RN-03
  Scenario: Rechazar una orden que trae el total desde el cliente
    Given path 'orders'
    And request { cliente: 'Ana', productos: [{ id: 'P001', cantidad: 1, valorUnitario: 1000 }], total: 1 }
    When method post
    Then status 422

  # Justificación: RN-01 y RN-02 son la primera barrera de calidad de datos; se
  # verifican también contra la API desplegada, no solo en pruebas unitarias.
  @RN-01 @RN-02
  Scenario Outline: Rechazar una orden inválida: <caso>
    Given path 'orders'
    And request <payload>
    When method post
    Then status 422
    And match karate.response.header('Content-Type') contains 'application/problem+json'
    And match response.status == 422

    Examples:
      | caso                 | payload                                                                          |
      | sin productos        | { cliente: 'Ana', productos: [] }                                                |
      | cantidad cero        | { cliente: 'Ana', productos: [{ id: 'P1', cantidad: 0, valorUnitario: 1000 }] }  |
      | cantidad negativa    | { cliente: 'Ana', productos: [{ id: 'P1', cantidad: -1, valorUnitario: 1000 }] } |
      | sin cliente          | { productos: [{ id: 'P1', cantidad: 1, valorUnitario: 1000 }] }                  |
```

---

## 6. src/test/java/ordenes/consultar-orden.feature

```gherkin
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
```

---

## 7. src/test/java/ordenes/transiciones.feature

```gherkin
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

  # Justificación: saltarse estados (CREADA → ENTREGADA) es la transición inválida
  # de mayor impacto: entregaría mercancía sin pago ni envío registrados.
  @RN-06
  Scenario: Rechazar una transición que se salta estados
    Given path 'orders', ordenId, 'status'
    And request { estado: 'ENTREGADA' }
    When method patch
    Then status 409
    And match response.codigo == 'RN-06'

  Scenario: Cancelar una orden creada
    Given path 'orders', ordenId
    When method delete
    Then status 200
    And match response.estado == 'CANCELADA'
```
