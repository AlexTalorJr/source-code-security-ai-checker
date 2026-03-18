# Phase 1: Foundation and Data Models - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish the project skeleton: config loading from config.yml with env var overrides, unified Finding and ScanResult data models with deterministic dedup fingerprints, SQLite persistence with WAL mode, FastAPI server with health endpoint, and Docker base image with all scanner tools. All subsequent phases build on this foundation.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

All areas in this phase are technical foundation decisions fully determined by the requirements. No user vision input needed — Claude has full discretion on:

- **Config structure** — config.yml organization, env var override mechanism, default values. Governed by INFRA-03 (config via env vars and config.yml) and INFRA-04 (no hardcoded credentials).
- **Finding model fields** — Field selection, severity enum, dedup fingerprint algorithm. Governed by SCAN-02 (unified severity: Critical/High/Medium/Low/Info) and SCAN-03 (stable fingerprints: file + rule + snippet hash).
- **Project layout** — Python package structure, module organization. Standard FastAPI project conventions.
- **Docker setup** — Base image, multi-stage build, scanner tool installation. Governed by INFRA-01 (single docker-compose up) and INFRA-05 (SQLite in mounted volume).
- **Database schema** — SQLite table design, WAL mode config, migration approach.
- **API skeleton** — FastAPI app structure, health endpoint response format. Governed by API-04.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — Full v1 requirements; Phase 1 covers SCAN-02, API-04, INFRA-01, INFRA-03, INFRA-04, INFRA-05
- `.planning/PROJECT.md` — Scanner tech stack, architecture layers, constraints, key decisions

### Phase scope
- `.planning/ROADMAP.md` — Phase 1 goal and success criteria (4 criteria that must be TRUE)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project, no existing code

### Established Patterns
- None yet — Phase 1 establishes the patterns all later phases follow

### Integration Points
- Config system will be consumed by every subsequent phase (scanners, AI, reports)
- Finding model is the core data contract — Phase 2 writes findings, Phases 3-5 read them
- SQLite schema must accommodate scan history (Phase 4) and false positive tracking (Phase 5)
- FastAPI app will be extended with scan endpoints (Phase 5) and dashboard (Phase 5)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. User confirmed all decisions in this phase are technical and deferred to Claude's discretion.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation-and-data-models*
*Context gathered: 2026-03-18*
