# Guia de Usuario

## Que es Security AI Scanner?

Una herramienta de escaneo de seguridad que analiza el codigo fuente en busca de vulnerabilidades utilizando doce herramientas de escaneo de seguridad en paralelo, enriquece los hallazgos con analisis de IA a traves de Claude, y produce informes accionables con sugerencias de correccion. Los escaneres se activan automaticamente segun los lenguajes detectados en el proyecto.

## Escaneres compatibles

### Semgrep (SAST multilenguaje)

**Language:** Python, PHP, JavaScript, TypeScript, Go, Java, Kotlin, Ruby, C#, Rust
**Type:** SAST
**Que detecta:** Fallas de inyeccion, problemas de autenticacion, patrones inseguros y vulnerabilidades especificas de lenguajes mediante coincidencia de patrones semanticos.
**Ejemplo de hallazgo:**
> `python.lang.security.audit.exec-detected`: Use of exec() detected at `app.py:42`

**Activado:** Automaticamente cuando se detectan archivos Python, PHP, JS/TS, Go, Java, Kotlin, Ruby, C# o Rust

### cppcheck (C/C++)

**Language:** C/C++
**Type:** SAST
**Que detecta:** Problemas de seguridad de memoria, desbordamientos de bufer, desreferencia de punteros nulos, comportamiento indefinido y fugas de recursos.
**Ejemplo de hallazgo:**
> `arrayIndexOutOfBounds`: Array index out of bounds at `buffer.cpp:15`

**Activado:** Automaticamente cuando se detectan archivos C/C++

### Gitleaks (secretos)

**Language:** Todos los lenguajes
**Type:** Deteccion de secretos
**Que detecta:** Secretos codificados, claves API, tokens, contrasenas y credenciales en el codigo fuente y el historial de git.
**Ejemplo de hallazgo:**
> `generic-api-key`: Generic API Key detected at `config.py:8`

**Activado:** Siempre activado para todos los proyectos

### Trivy (infraestructura)

**Language:** Docker, Terraform, YAML/Kubernetes
**Type:** SCA / Infrastructure
**Que detecta:** CVE en imagenes de contenedor, configuraciones incorrectas de IaC y problemas de seguridad de Kubernetes.
**Ejemplo de hallazgo:**
> `CVE-2023-44487`: HTTP/2 rapid reset attack in `Dockerfile:1`

**Activado:** Automaticamente cuando se detectan Dockerfiles, Terraform o Kubernetes YAML

### Checkov (infraestructura)

**Language:** Docker, Terraform, YAML, CI configs
**Type:** Infrastructure
**Que detecta:** Mejores practicas de seguridad de Infrastructure-as-code, configuraciones incorrectas de nube y seguridad de pipelines CI.
**Ejemplo de hallazgo:**
> `CKV_DOCKER_2`: Ensure that HEALTHCHECK instructions have been added to container images at `Dockerfile:1`

**Activado:** Automaticamente cuando se detectan archivos Docker, Terraform, YAML o CI

### Psalm (PHP)

**Language:** PHP
**Type:** SAST (analisis de contaminacion)
**Que detecta:** Inyeccion SQL, XSS y otras vulnerabilidades relacionadas con contaminacion a traves del rastreo del flujo de datos en codigo PHP.
**Ejemplo de hallazgo:**
> `TaintedSql`: Detected tainted SQL in `UserController.php:34`

**Activado:** Automaticamente cuando se detectan archivos PHP

### Enlightn (Laravel)

**Language:** Laravel (PHP)
**Type:** SAST
**Que detecta:** Vulnerabilidades CSRF, mass assignment, modo de depuracion expuesto, archivos .env expuestos y mas de 120 verificaciones de seguridad especificas de Laravel.
**Ejemplo de hallazgo:**
> `MassAssignmentAnalyzer`: Potential mass assignment vulnerability in `User.php:12`

**Activado:** Automaticamente cuando se detecta un proyecto Laravel

### PHP Security Checker (PHP SCA)

**Language:** PHP (Composer)
**Type:** SCA
**Que detecta:** CVE conocidas en dependencias de Composer consultando la base de datos de avisos de seguridad de SensioLabs.
**Ejemplo de hallazgo:**
> `CVE-2023-46734`: Twig code injection via sandbox bypass in `composer.lock`

**Activado:** Automaticamente cuando se detectan archivos PHP Composer

### gosec (Go SAST)

**Language:** Go
**Type:** SAST
**Que detecta:** Credenciales codificadas, inyeccion SQL, criptografia insegura, permisos de archivo inseguros y problemas de seguridad especificos de Go.
**Ejemplo de hallazgo:**
> `G101`: Potential hardcoded credentials at `config.go:22`

**Activado:** Automaticamente cuando se detectan archivos Go

### Bandit (Python SAST)

**Language:** Python
**Type:** SAST
**Que detecta:** Contrasenas codificadas, inyeccion SQL, uso de eval, criptografia debil y patrones de seguridad especificos de Python.
**Ejemplo de hallazgo:**
> `B105`: Possible hardcoded password at `settings.py:15`

**Activado:** Automaticamente cuando se detectan archivos Python

### Brakeman (Ruby/Rails SAST)

**Language:** Ruby / Rails
**Type:** SAST
**Que detecta:** Inyeccion SQL, XSS, mass assignment, inyeccion de comandos y vulnerabilidades especificas de Rails.
**Ejemplo de hallazgo:**
> `SQL Injection`: Possible SQL injection near line 15 in `app/models/user.rb`

**Activado:** Automaticamente cuando se detectan archivos Ruby

### cargo-audit (Rust SCA)

**Language:** Rust
**Type:** SCA
**Que detecta:** Dependencias vulnerables conocidas a traves de la base de datos RustSec mediante la auditoria de archivos Cargo.lock.
**Ejemplo de hallazgo:**
> `RUSTSEC-2019-0009`: Heap overflow in smallvec in `Cargo.lock`

**Activado:** Automaticamente cuando se detectan archivos Rust

## Ejecutar un Escaneo

### Via API

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/your-org/repo.git", "branch": "main"}'
```

La API devuelve un ID de escaneo de inmediato (202 Accepted). El escaneo se ejecuta de forma asincrona en la cola en segundo plano.

### Via CLI

```bash
scanner scan --repo-url https://github.com/your-org/repo.git --branch main
```

El CLI ejecuta el escaneo directamente e imprime los resultados en stdout. Use `--format html` o `--format pdf` para generar archivos de informe.

### Via Panel de Control

Navegue a `http://localhost:8000/dashboard`, complete la URL del repositorio y la rama, y envie el formulario. El panel de control muestra el progreso del escaneo y los resultados en linea.

## Comprension de los Niveles de Severidad

| Nivel | Significado | Accion |
|-------|---------|--------|
| **CRITICAL** | Riesgo de explotacion inmediata (p. ej., inyeccion SQL, RCE) | Corregir de inmediato; bloquea el despliegue |
| **HIGH** | Vulnerabilidad grave (p. ej., omision de autenticacion, secretos en el codigo) | Corregir antes del lanzamiento |
| **MEDIUM** | Riesgo moderado (p. ej., criptografia debil, encabezados faltantes) | Corregir en el sprint actual |
| **LOW** | Problema menor (p. ej., mensajes de error detallados) | Corregir cuando sea conveniente |
| **INFO** | Hallazgo informativo (p. ej., uso de API obsoleta) | Revisar, no requiere accion |

## Informes

### Informes HTML

Los informes HTML interactivos incluyen:

- **Seccion de resumen** -- total de hallazgos, desglose por severidad, resultado del quality gate
- **Tabla de hallazgos con filtros** -- filtre por severidad, herramienta, ruta de archivo
- **Contexto de codigo** -- fragmentos de codigo fuente con lineas vulnerables resaltadas
- **Sugerencias de correccion con IA** -- codigo de correccion generado por Claude con explicaciones
- **Riesgos compuestos** -- hallazgos de correlacion entre herramientas identificados por IA
- **Graficos** -- grafico circular de distribucion de severidad y grafico de barras de hallazgos por herramienta

Acceda a los informes HTML via `GET /api/scans/{id}/report/html` o desde el panel de control.

### Informes PDF

Los informes PDF proporcionan un documento formal adecuado para revision gerencial:

- **Resumen ejecutivo** -- metadatos del escaneo, recuentos de severidad, resultado del gate
- **Graficos** -- graficos PNG embebidos (distribucion de severidad, desglose por herramienta)
- **Hallazgos detallados** -- agrupados por severidad con fragmentos de codigo
- **Seccion de riesgos compuestos** -- vulnerabilidades entre componentes identificadas por IA

Acceda a los informes PDF via `GET /api/scans/{id}/report/pdf`.

## Quality Gate

El quality gate evalua los resultados del escaneo frente a umbrales de severidad configurados. Por defecto, cualquier hallazgo CRITICAL o HIGH hace que el gate falle.

- **pass** -- ningun hallazgo en o por encima del umbral de severidad configurado
- **fail** -- uno o mas hallazgos en o por encima del umbral, o riesgos compuestos con severidad Critical/High cuando `include_compound_risks` esta habilitado

Los resultados del quality gate estan disponibles via `GET /api/scans/{id}/gate` y se muestran en los informes y el panel de control.

## Analisis con IA

Cada lote de hallazgos se envia a Claude para analisis contextual:

- **Revision contextual** -- comprension de lo que hace el codigo y si el hallazgo es un verdadero positivo
- **Sugerencias de correccion** -- cambios de codigo concretos para remediar la vulnerabilidad
- **Riesgos compuestos** -- identificacion de cadenas de ataque que abarcan multiples hallazgos (p. ej., omision de autenticacion + IDOR = toma de cuenta)

El costo del analisis con IA por escaneo se registra y esta limitado por `ai.max_cost_per_scan` en la configuracion.

## Comparacion Delta

Cuando un repositorio ha sido escaneado anteriormente, el escaner calcula automaticamente un delta:

- **Hallazgos nuevos** -- vulnerabilidades no presentes en el escaneo anterior
- **Hallazgos corregidos** -- vulnerabilidades del escaneo anterior que ya no estan presentes
- **Hallazgos persistentes** -- vulnerabilidades presentes en ambos escaneos

El delta se calcula comparando los fingerprints entre el escaneo actual y el escaneo previo mas reciente del mismo repositorio y rama. El primer escaneo no devuelve delta (no hay linea base previa).

## Gestion de Falsos Positivos

### Via Panel de Control

Desde la vista de hallazgos, haga clic en el boton de supresion de cualquier hallazgo. Proporcione una razon para la supresion.

### Via API

```bash
curl -X POST http://localhost:8000/api/suppressions \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"fingerprint": "<finding-fingerprint>", "reason": "False positive: test fixture"}'
```

Los hallazgos suprimidos quedan excluidos de la evaluacion del quality gate y se marcan en los informes.

## Inicio de Sesion en el Panel de Control

### Iniciar sesion

1. Navegue a `/dashboard/login`
2. Ingrese el nombre de usuario y contrasena proporcionados por su administrador
3. Haga clic en "Iniciar sesion"

Su sesion se mantiene mediante una cookie con expiracion de 7 dias.

### Cerrar sesion

Haga clic en "Cerrar sesion" en la barra de navegacion en la parte superior de cualquier pagina del panel de control.

## Uso de Perfiles de Escaneo

### Que son los perfiles de escaneo?

Los perfiles de escaneo son configuraciones de escaneres predefinidas creadas por los administradores. Cada perfil especifica que escaneres ejecutar y con que parametros.

### Seleccion de un perfil en el panel de control

Al iniciar un escaneo desde el panel de control, use la lista desplegable de perfiles sobre el boton "Iniciar Escaneo". Seleccione un nombre de perfil o elija "(Sin perfil)" para usar la configuracion predeterminada.

### Seleccion de un perfil via API

Agregue el campo `profile` al cuerpo de su solicitud de escaneo:

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo.git", "profile": "quick_scan"}'
```

Sin perfil especificado, se aplica la configuracion base de escaneres de `config.yml`.

### Nombre del perfil en el historial de escaneos

El nombre del perfil utilizado para cada escaneo se muestra en la tabla del historial de escaneos.

## Escaneo DAST

### Que es DAST?

El Testeo Dinamico de Seguridad de Aplicaciones (DAST) escanea aplicaciones web en ejecucion en busca de vulnerabilidades enviando solicitudes HTTP y analizando las respuestas. A diferencia del SAST (que analiza el codigo fuente), DAST prueba las aplicaciones mientras se ejecutan.

### Como iniciar un escaneo DAST

Proporcione un `target_url` en lugar de `path` o `repo_url` al iniciar un escaneo.

**Via API:**

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com"}'
```

**Via panel de control:** Ingrese la URL objetivo en el formulario de inicio de escaneo. El campo `target_url` es exclusivo con `path` y `repo_url`.

### Resultados DAST

Los resultados DAST incluyen:

- **Niveles de severidad** -- critical, high, medium, low, info
- **Identificadores de plantilla** -- identificadores de plantillas Nuclei que describen el tipo de vulnerabilidad
- **Hallazgos basados en URL** -- cada hallazgo referencia la URL objetivo donde se detecto la vulnerabilidad

Los resultados DAST aparecen en los informes junto con los resultados SAST y estan sujetos a la misma evaluacion del quality gate.
