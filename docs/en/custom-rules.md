# Custom Rules Guide

## Overview

This guide covers writing custom Semgrep rules for the aipix platform components. Custom rules allow detection of platform-specific vulnerabilities that generic rules miss.

## Target Components

| Component | Language | Key Concerns |
|-----------|----------|-------------|
| VMS (Video Management) | PHP/Laravel | SQL injection, broken auth, IDOR |
| Mediaserver | C++ | Buffer overflow, format strings, memory safety |
| REST API | PHP/Laravel | API token exposure, SSRF, mass assignment |
| Webhooks | PHP | Missing signature verification |
| Desktop Client | C# | Insecure deserialization, credential storage |

## Semgrep Rule Format

Semgrep rules are YAML files with pattern matching definitions. Each rule specifies:

- **id** -- unique rule identifier (use `aipix.` prefix for custom rules)
- **pattern** -- code pattern to match (supports metavariables like `$VAR`)
- **message** -- human-readable description of the finding
- **severity** -- `ERROR` (Critical/High), `WARNING` (Medium), or `INFO` (Low/Info)
- **languages** -- list of languages the rule applies to

## Rule File Location

Custom rules are stored in the `rules/` directory at the project root. The Semgrep adapter automatically loads all `.yml` files from this directory alongside the default rule set.

```
rules/
  aipix-rtsp-auth.yml
  aipix-api-security.yml
  aipix-memory-safety.yml
```

## Example Rules

### RTSP Hardcoded Credentials

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

### API Token in Log Output

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

### Missing Webhook Signature Verification

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

### SQL Injection via Raw Query

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

## Testing Rules

Test custom rules against sample code before deploying:

```bash
# Test a single rule file against a target directory
semgrep --config rules/aipix-rtsp-auth.yml /path/to/code

# Test all custom rules
semgrep --config rules/ /path/to/code

# Dry run (show matches without full output)
semgrep --config rules/ --json /path/to/code | python3 -m json.tool
```

## Rule Development Tips

1. **Start specific, broaden later** -- begin with exact patterns and relax constraints as needed
2. **Use metavariables** -- `$VAR` matches any expression, `$...ARGS` matches multiple arguments
3. **Test with real code** -- use actual aipix source files to validate rules
4. **Set appropriate severity** -- `ERROR` for exploitable issues, `WARNING` for potential risks, `INFO` for code quality
5. **Add metadata** -- `category` and `component` fields help with filtering and reporting
