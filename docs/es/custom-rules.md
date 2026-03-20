# Guía de Reglas Personalizadas

## Descripción General

Esta guía cubre la escritura de reglas Semgrep personalizadas para los componentes de la plataforma aipix. Las reglas personalizadas permiten detectar vulnerabilidades específicas de la plataforma que las reglas genéricas no detectan.

## Componentes Objetivo

| Componente | Lenguaje | Preocupaciones Principales |
|-----------|----------|-------------|
| VMS (Video Management) | PHP/Laravel | Inyección SQL, autenticación rota, IDOR |
| Mediaserver | C++ | Desbordamiento de búfer, cadenas de formato, seguridad de memoria |
| REST API | PHP/Laravel | Exposición de tokens API, SSRF, asignación masiva |
| Webhooks | PHP | Falta de verificación de firma |
| Desktop Client | C# | Deserialización insegura, almacenamiento de credenciales |

## Formato de Regla Semgrep

Las reglas Semgrep son archivos YAML con definiciones de coincidencia de patrones. Cada regla especifica:

- **id** -- identificador único de la regla (use el prefijo `aipix.` para reglas personalizadas)
- **pattern** -- patrón de código a coincidir (admite metavariables como `$VAR`)
- **message** -- descripción legible por humanos del hallazgo
- **severity** -- `ERROR` (Critical/High), `WARNING` (Medium), o `INFO` (Low/Info)
- **languages** -- lista de lenguajes a los que aplica la regla

## Ubicación de los Archivos de Reglas

Las reglas personalizadas se almacenan en el directorio `rules/` en la raíz del proyecto. El adaptador Semgrep carga automáticamente todos los archivos `.yml` de este directorio junto al conjunto de reglas predeterminado.

```
rules/
  aipix-rtsp-auth.yml
  aipix-api-security.yml
  aipix-memory-safety.yml
```

## Reglas de Ejemplo

### Credenciales RTSP Embebidas en el Código

```yaml
rules:
  - id: aipix.rtsp-hardcoded-credentials
    pattern: rtsp://$USER:$PASS@$HOST
    message: "Hardcoded RTSP credentials detected"
    severity: ERROR
    languages: [php, python, yaml]
    metadata:
      category: authentication
      component: mediaserver
```

### Token API en la Salida del Log

```yaml
rules:
  - id: aipix.api-token-in-log
    patterns:
      - pattern: |
          Log::$METHOD(..., $TOKEN, ...)
      - metavariable-regex:
          metavariable: $TOKEN
          regex: ".*token.*|.*api_key.*|.*secret.*"
    message: "Possible API token logged -- check for sensitive data exposure"
    severity: WARNING
    languages: [php]
    metadata:
      category: data-exposure
      component: vms
```

### Falta de Verificación de Firma en Webhook

```yaml
rules:
  - id: aipix.webhook-no-signature-check
    patterns:
      - pattern: |
          function $HANDLER(Request $request) {
            ...
          }
      - pattern-not: |
          function $HANDLER(Request $request) {
            ...
            $request->header('X-Signature', ...)
            ...
          }
    message: "Webhook handler missing signature verification"
    severity: ERROR
    languages: [php]
    metadata:
      category: authentication
      component: webhooks
```

### Inyección SQL vía Consulta Raw

```yaml
rules:
  - id: aipix.sql-injection-raw
    patterns:
      - pattern: DB::raw("..." . $VAR . "...")
    message: "Potential SQL injection via string concatenation in raw query"
    severity: ERROR
    languages: [php]
    metadata:
      category: injection
      component: vms
```

## Prueba de Reglas

Pruebe las reglas personalizadas contra código de muestra antes de desplegarlas:

```bash
# Test a single rule file against a target directory
semgrep --config rules/aipix-rtsp-auth.yml /path/to/code

# Test all custom rules
semgrep --config rules/ /path/to/code

# Dry run (show matches without full output)
semgrep --config rules/ --json /path/to/code | python3 -m json.tool
```

## Consejos para el Desarrollo de Reglas

1. **Comience específico, amplíe después** -- inicie con patrones exactos y relaje las restricciones según sea necesario
2. **Use metavariables** -- `$VAR` coincide con cualquier expresión, `$...ARGS` coincide con múltiples argumentos
3. **Pruebe con código real** -- use archivos fuente reales de aipix para validar las reglas
4. **Establezca la severidad adecuada** -- `ERROR` para problemas explotables, `WARNING` para riesgos potenciales, `INFO` para calidad del código
5. **Agregue metadatos** -- los campos `category` y `component` ayudan con el filtrado y la generación de informes
