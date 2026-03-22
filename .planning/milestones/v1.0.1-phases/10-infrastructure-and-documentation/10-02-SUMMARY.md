---
phase: 10-infrastructure-and-documentation
plan: 02
subsystem: docs
tags: [documentation, scanners, plugin-registry, user-guide, admin-guide]

requires:
  - phase: 08-plugin-registry-architecture
    provides: config-driven plugin registry with adapter_class
  - phase: 09-tier-1-scanner-adapters
    provides: gosec, bandit, brakeman, cargo-audit adapters
provides:
  - Updated English documentation for all 12 scanners
  - Plugin Registry section in admin-guide
  - Scanner cards in user-guide for all 12 tools
  - /api/scanners endpoint documented in api.md
affects: [10-03-translated-docs]

tech-stack:
  added: []
  patterns: [per-scanner card format in user-guide, plugin registry docs in admin-guide]

key-files:
  created: []
  modified:
    - docs/en/user-guide.md
    - docs/en/admin-guide.md
    - docs/en/devops-guide.md
    - docs/en/architecture.md
    - docs/en/api.md
    - docs/en/custom-rules.md
    - docs/en/database-schema.md
    - docs/en/transfer-guide.md
    - README.md

key-decisions:
  - "Per-scanner card format with Language/Type/Detection/Example/Enabled fields for consistency"
  - "Plugin Registry docs placed in admin-guide.md rather than separate file"

patterns-established:
  - "Scanner card format: Name (Language), Type, What it detects, Example finding, Enabled condition"

requirements-completed: [DOCS-01]

duration: 4min
completed: 2026-03-22
---

# Phase 10 Plan 02: English Documentation Update Summary

**Updated all 8 English docs and README.md to reflect 12 scanners with per-scanner cards, Plugin Registry section, and /api/scanners endpoint**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-22T08:21:50Z
- **Completed:** 2026-03-22T08:26:04Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- user-guide.md now has 12 per-scanner cards with consistent format (Language, Type, Detection, Example, Enabled)
- admin-guide.md has full Plugin Registry section with adapter_class docs and how-to-add-scanner guide
- devops-guide.md documents all 12 scanner binaries in Docker with install methods and verify-scanners target
- architecture.md mermaid diagram updated with all 12 adapters and ScannerRegistry node
- api.md documents /api/scanners endpoint with example response
- custom-rules.md adds gosec, Bandit, Brakeman custom rule configuration
- README.md updated to 12 scanners with full scanner table

## Task Commits

Each task was committed atomically:

1. **Task 1: Update user-guide.md, admin-guide.md, devops-guide.md** - `1ff9c7e` (feat)
2. **Task 2: Update remaining 5 English docs and README.md** - `f0bfff9` (feat)

## Files Created/Modified
- `docs/en/user-guide.md` - Added Supported Scanners section with 12 scanner cards
- `docs/en/admin-guide.md` - Updated scanner config to 12, added Plugin Registry section
- `docs/en/devops-guide.md` - Added Scanner Binaries table, verify-scanners docs, multi-arch notes
- `docs/en/architecture.md` - Updated mermaid diagrams with 12 adapters and ScannerRegistry
- `docs/en/api.md` - Added /api/scanners endpoint documentation
- `docs/en/custom-rules.md` - Added gosec, Bandit, Brakeman custom rule sections
- `docs/en/database-schema.md` - Updated tool enum to 12 scanners
- `docs/en/transfer-guide.md` - Updated scanner verification to reference all 12 tools
- `README.md` - Updated to 12 scanners with full table and plugin registry mention

## Decisions Made
- Per-scanner card format uses consistent fields (Language, Type, What it detects, Example finding, Enabled) across all 12 scanners
- Plugin Registry documentation placed in admin-guide.md as a natural extension of Scanner Configuration section

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- English source content complete for all 12 scanners
- Ready for Plan 03 (translated documentation) to mirror these English files into RU, FR, ES, IT

## Self-Check: PASSED

All 9 modified files exist. Both task commits (1ff9c7e, f0bfff9) verified in git log.

---
*Phase: 10-infrastructure-and-documentation*
*Completed: 2026-03-22*
