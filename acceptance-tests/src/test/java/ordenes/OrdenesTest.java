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
