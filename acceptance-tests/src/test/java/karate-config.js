function fn() {
  var baseUrl = karate.properties['baseUrl'] || 'http://localhost:8080';
  karate.log('baseUrl =', baseUrl);
  karate.configure('connectTimeout', 5000);
  karate.configure('readTimeout', 10000);
  // Cada escenario envía su propio X-Request-ID para cruzarlo con los logs de la API.
  karate.configure('headers', { 'X-Request-ID': 'karate-' + java.util.UUID.randomUUID() });
  return {
    baseUrl: baseUrl,
    crearOrden: 'classpath:ordenes/helpers/crear-orden.feature',
    cambiarEstado: 'classpath:ordenes/helpers/cambiar-estado.feature'
  };
}
