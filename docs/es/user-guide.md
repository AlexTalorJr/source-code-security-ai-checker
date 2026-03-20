# Guía de Usuario

## ¿Qué es Security AI Scanner?

Una herramienta de escaneo de seguridad que analiza el código fuente en busca de vulnerabilidades utilizando cinco herramientas de análisis estático en paralelo, enriquece los hallazgos con análisis de IA a través de Claude, y produce informes accionables con sugerencias de corrección.

## Ejecutar un Escaneo

### Vía API

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/your-org/repo.git", "branch": "main"}'
```

La API devuelve un ID de escaneo de inmediato (202 Accepted). El escaneo se ejecuta de forma asíncrona en la cola en segundo plano.

### Vía CLI

```bash
scanner scan --repo-url https://github.com/your-org/repo.git --branch main
```

El CLI ejecuta el escaneo directamente e imprime los resultados en stdout. Use `--format html` o `--format pdf` para generar archivos de informe.

### Vía Panel de Control

Navegue a `http://localhost:8000/dashboard`, complete la URL del repositorio y la rama, y envíe el formulario. El panel de control muestra el progreso del escaneo y los resultados en línea.

## Comprensión de los Niveles de Severidad

| Nivel | Significado | Acción |
|-------|---------|--------|
| **CRITICAL** | Riesgo de explotación inmediata (p. ej., inyección SQL, RCE) | Corregir de inmediato; bloquea el despliegue |
| **HIGH** | Vulnerabilidad grave (p. ej., omisión de autenticación, secretos en el código) | Corregir antes del lanzamiento |
| **MEDIUM** | Riesgo moderado (p. ej., criptografía débil, encabezados faltantes) | Corregir en el sprint actual |
| **LOW** | Problema menor (p. ej., mensajes de error detallados) | Corregir cuando sea conveniente |
| **INFO** | Hallazgo informativo (p. ej., uso de API obsoleta) | Revisar, no requiere acción |

## Informes

### Informes HTML

Los informes HTML interactivos incluyen:

- **Sección de resumen** -- total de hallazgos, desglose por severidad, resultado del quality gate
- **Tabla de hallazgos con filtros** -- filtre por severidad, herramienta, ruta de archivo
- **Contexto de código** -- fragmentos de código fuente con líneas vulnerables resaltadas
- **Sugerencias de corrección con IA** -- código de corrección generado por Claude con explicaciones
- **Riesgos compuestos** -- hallazgos de correlación entre herramientas identificados por IA
- **Gráficos** -- gráfico circular de distribución de severidad y gráfico de barras de hallazgos por herramienta

Acceda a los informes HTML vía `GET /api/scans/{id}/report/html` o desde el panel de control.

### Informes PDF

Los informes PDF proporcionan un documento formal adecuado para revisión gerencial:

- **Resumen ejecutivo** -- metadatos del escaneo, recuentos de severidad, resultado del gate
- **Gráficos** -- gráficos PNG embebidos (distribución de severidad, desglose por herramienta)
- **Hallazgos detallados** -- agrupados por severidad con fragmentos de código
- **Sección de riesgos compuestos** -- vulnerabilidades entre componentes identificadas por IA

Acceda a los informes PDF vía `GET /api/scans/{id}/report/pdf`.

## Quality Gate

El quality gate evalúa los resultados del escaneo frente a umbrales de severidad configurados. Por defecto, cualquier hallazgo CRITICAL o HIGH hace que el gate falle.

- **pass** -- ningún hallazgo en o por encima del umbral de severidad configurado
- **fail** -- uno o más hallazgos en o por encima del umbral, o riesgos compuestos con severidad Critical/High cuando `include_compound_risks` está habilitado

Los resultados del quality gate están disponibles vía `GET /api/scans/{id}/gate` y se muestran en los informes y el panel de control.

## Análisis con IA

Cada lote de hallazgos se envía a Claude para análisis contextual:

- **Revisión contextual** -- comprensión de lo que hace el código y si el hallazgo es un verdadero positivo
- **Sugerencias de corrección** -- cambios de código concretos para remediar la vulnerabilidad
- **Riesgos compuestos** -- identificación de cadenas de ataque que abarcan múltiples hallazgos (p. ej., omisión de autenticación + IDOR = toma de cuenta)

El costo del análisis con IA por escaneo se registra y está limitado por `ai.max_cost_per_scan` en la configuración.

## Comparación Delta

Cuando un repositorio ha sido escaneado anteriormente, el escáner calcula automáticamente un delta:

- **Hallazgos nuevos** -- vulnerabilidades no presentes en el escaneo anterior
- **Hallazgos corregidos** -- vulnerabilidades del escaneo anterior que ya no están presentes
- **Hallazgos persistentes** -- vulnerabilidades presentes en ambos escaneos

El delta se calcula comparando los fingerprints entre el escaneo actual y el escaneo previo más reciente del mismo repositorio y rama. El primer escaneo no devuelve delta (no hay línea base previa).

## Gestión de Falsos Positivos

### Vía Panel de Control

Desde la vista de hallazgos, haga clic en el botón de supresión de cualquier hallazgo. Proporcione una razón para la supresión.

### Vía API

```bash
curl -X POST http://localhost:8000/api/suppressions \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"fingerprint": "<finding-fingerprint>", "reason": "False positive: test fixture"}'
```

Los hallazgos suprimidos quedan excluidos de la evaluación del quality gate y se marcan en los informes.
