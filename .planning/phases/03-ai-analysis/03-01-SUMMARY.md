---
phase: 03-ai-analysis
plan: 01
subsystem: ai
tags: [pydantic, claude, anthropic, sqlalchemy, cost-tracking, prompt-engineering]

# Dependency graph
requires:
  - phase: 01-project-foundation
    provides: "Base ORM model, ScannerSettings, FindingSchema, Severity enum"
  - phase: 02-scanner-adapters-and-orchestration
    provides: "ScanResult model, Finding model, config.yml.example structure"
provides:
  - "AI response schemas (FindingAnalysis, ComponentAnalysisResponse, CorrelationResponse, AIAnalysisResult)"
  - "System prompt builders with aipix security context and framework mapping"
  - "Cost estimation and budget checking functions"
  - "CompoundRisk ORM model with join table for cross-tool correlation"
  - "AIConfig nested in ScannerSettings"
  - "ANALYSIS_TOOL and CORRELATION_TOOL dicts for Claude tool_use"
affects: [03-02-PLAN, 03-03-PLAN, 04-reporting, 05-dashboard]

# Tech tracking
tech-stack:
  added: [anthropic>=0.86.0]
  patterns: [tool_use structured output, Literal type for enum validation, component-based prompt dispatch]

key-files:
  created:
    - src/scanner/ai/__init__.py
    - src/scanner/ai/schemas.py
    - src/scanner/ai/prompts.py
    - src/scanner/ai/cost.py
    - src/scanner/models/compound_risk.py
    - src/scanner/schemas/compound_risk.py
    - tests/phase_03/__init__.py
    - tests/phase_03/conftest.py
    - tests/phase_03/test_schemas.py
    - tests/phase_03/test_prompts.py
    - tests/phase_03/test_cost.py
    - tests/phase_03/test_compound_risk_model.py
  modified:
    - src/scanner/config.py
    - src/scanner/models/scan.py
    - src/scanner/schemas/scan.py
    - pyproject.toml
    - config.yml.example

key-decisions:
  - "Literal type for risk_category enum validation (not Python Enum) for Pydantic JSON compatibility"
  - "CompoundRisk schema uses str severity (from Claude) while ORM uses int (maps to Severity IntEnum)"
  - "COMPONENT_FRAMEWORK_MAP uses startswith matching for component name prefixes"

patterns-established:
  - "AI tool dicts follow Claude tool_use format with input_schema for structured output"
  - "Component prompt builders serialize findings to JSON with specific field subset"
  - "Budget cutoff at 80% of max_cost to avoid overshoot"

requirements-completed: [AI-01, AI-02, AI-03, AI-04]

# Metrics
duration: 5min
completed: 2026-03-19
---

# Phase 03 Plan 01: AI Analysis Foundation Summary

**Pydantic response schemas, prompt builders with aipix security context, cost calculator at Sonnet 4.6 rates, and CompoundRisk DB model with join table**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-19T09:03:12Z
- **Completed:** 2026-03-19T09:08:00Z
- **Tasks:** 2
- **Files modified:** 17

## Accomplishments
- AI response schemas (FindingAnalysis with 8 risk categories, ComponentAnalysisResponse, CorrelationResponse, AIAnalysisResult) with full Pydantic validation
- System prompt builders with aipix-specific security concerns and framework context for 5 components (vms/Laravel, mediaserver/C++, infra/K8s, client/C#, mobile/Flutter)
- Cost estimation and budget checking at $3/$15 per MTok with 80% budget cutoff
- CompoundRisk ORM model with compound_risk_findings join table for cross-tool correlation
- AIConfig nested in ScannerSettings with sensible defaults (max_cost=5.0, model=claude-sonnet-4-6)
- 38 passing tests across 4 test files

## Task Commits

Each task was committed atomically:

1. **Task 1: AI config, response schemas, prompts, and cost module** - `d9c9e77` (feat)
2. **Task 2: Compound risk DB models and ScanResult extension** - `f9c3394` (feat)

## Files Created/Modified
- `src/scanner/ai/__init__.py` - Module exports for AI schemas
- `src/scanner/ai/schemas.py` - Pydantic models for AI response validation (FindingAnalysis, FixSuggestion, ComponentAnalysisResponse, CorrelationResponse, AIAnalysisResult)
- `src/scanner/ai/prompts.py` - System prompt builders with aipix security concerns and tool definitions
- `src/scanner/ai/cost.py` - Token-to-USD cost calculation and budget checking
- `src/scanner/models/compound_risk.py` - CompoundRisk ORM model and compound_risk_findings join table
- `src/scanner/schemas/compound_risk.py` - CompoundRiskSchema Pydantic model
- `src/scanner/config.py` - Added AIConfig model nested in ScannerSettings
- `src/scanner/models/scan.py` - Added ai_cost_usd column and compound_risks relationship
- `src/scanner/schemas/scan.py` - Added ai_cost_usd, ai_skipped, ai_skip_reason fields
- `pyproject.toml` - Added anthropic>=0.86.0 dependency
- `config.yml.example` - Added ai section with defaults

## Decisions Made
- Used Literal type for risk_category validation instead of Python Enum for cleaner JSON serialization in Pydantic
- CompoundRisk schema uses string severity (matching Claude output) while ORM stores integer (mapping to Severity IntEnum)
- Component matching uses startswith on COMPONENT_FRAMEWORK_MAP keys for flexible prefix matching

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test assertion for unknown component prompt**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Test checked "C++" not in prompt for unknown components, but "C++" appears in core AIPIX_SECURITY_CONCERNS constant (item 6: "C++ Mediaserver memory safety")
- **Fix:** Changed test to check for framework-specific terms ("Eloquent", "use-after-free") instead of "C++" which is part of core concerns
- **Files modified:** tests/phase_03/test_prompts.py
- **Committed in:** d9c9e77 (Task 1 commit)

**2. [Rule 1 - Bug] Fixed test parameter name mismatch**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Test used `estimated=0.5` but function parameter is `estimated_next`
- **Fix:** Updated test to use correct parameter name `estimated_next`
- **Files modified:** tests/phase_03/test_cost.py
- **Committed in:** d9c9e77 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs in test specs)
**Impact on plan:** Both fixes corrected test expectations to match correct implementation. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All AI data contracts and schemas defined, ready for AIAnalyzer implementation (Plan 02)
- Prompt builders ready for Claude API integration
- Cost tracking infrastructure ready for per-scan cost recording
- CompoundRisk DB model ready for cross-component correlation storage

---
*Phase: 03-ai-analysis*
*Completed: 2026-03-19*
