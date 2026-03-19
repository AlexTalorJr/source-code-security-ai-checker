# Phase 3: AI Analysis - Research

**Researched:** 2026-03-19
**Domain:** Anthropic Claude API integration for security finding enrichment
**Confidence:** HIGH

## Summary

Phase 3 enriches deduplicated scan findings with Claude API-powered semantic analysis. The architecture involves batching findings by component (top-level directory), sending each batch as a separate API call to Claude Sonnet 4.6 for business logic risk identification and fix suggestions, then running a final cross-component correlation call. Token budgeting enforces the $5/scan cost ceiling by prioritizing Critical/High findings and stopping at 80% budget consumption.

The Anthropic Python SDK (v0.86.0) provides first-class async support via `AsyncAnthropic`, built-in token counting via `client.messages.count_tokens()` (GA, free endpoint), and usage tracking in every response (`response.usage.input_tokens`, `response.usage.output_tokens`). Structured JSON output is achieved via the tool_use pattern, where Claude returns data conforming to a JSON schema defined in the tool's `input_schema`. No additional libraries are needed beyond `anthropic` itself.

**Primary recommendation:** Use `anthropic` SDK with `AsyncAnthropic` client. Use `messages.count_tokens()` for pre-estimation, tool_use for structured JSON responses, and `response.usage` for actual cost tracking. Batch findings by top-level directory, process in severity-priority order, and store compound risks in a dedicated DB table.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Batch findings by component using directory-based grouping (top-level directory maps to component)
- Each component batch is a separate API call to Claude
- Final cross-component correlation call after all component batches complete
- System prompt embeds aipix-specific security concerns from PROJECT.md (RTSP access, API tokens, tenant isolation, webhooks, K8s misconfig, C++ memory safety, IDOR)
- System prompt includes framework context per component (Laravel for PHP, STL for C++, Helm for infra)
- Finding snippet only -- no expanded source code context beyond what scanners captured (file_path, line, snippet, rule_id)
- Claude returns structured JSON responses (not free-form markdown)
- Severity-first priority: analyze Critical/High findings first, then Medium if budget remains, skip Low/Info
- Pre-estimate tokens per batch, sort batches by severity priority
- Stop sending batches when approaching ~80% of budget
- Budget limit configurable in config.yml (`ai.max_cost_per_scan`, default $5)
- Log actual cost from API response after each call
- Store per-scan AI cost in ScanResult DB record (new column) + show in CLI summary
- Report which components were analyzed vs skipped due to budget
- Separate final API call with per-component AI summaries as input for correlation
- Compound risk entries stored in dedicated DB table (`compound_risks`) with join table to findings
- Each compound risk has its own severity assigned by Claude
- Compound risk severity affects quality gate -- Critical/High compound risks fail the gate
- Compound risks reference findings by fingerprint
- Fix suggestion format: structured JSON with `before`, `after`, `explanation` fields
- Framework-specific fixes (Eloquent for Laravel, smart pointers for C++, etc.)
- When no concrete fix possible: `fix_suggestion` is null, textual `recommendation` with investigation steps
- Graceful degradation: scan completes without AI enrichment when Claude API unavailable
- AI fields remain null on findings, compound_risks table empty for that scan
- Report clearly indicates "AI analysis was skipped" with reason
- No retry loop -- single attempt per batch, fail fast on API errors

### Claude's Discretion
- Exact system prompt wording and few-shot examples
- JSON schema validation approach for Claude responses
- Token estimation algorithm (tiktoken vs character heuristic)
- Retry/backoff strategy for transient API errors (rate limits)
- Anthropic SDK version and async client setup
- Config.yml structure for AI section

### Deferred Ideas (OUT OF SCOPE)
- Web dashboard display of AI cost -- Phase 5 scope (DB column added in Phase 3)
- Visual diff rendering of before/after fixes -- Phase 4 scope (reports)
- Configurable system prompt in config.yml -- keep hardcoded for v1, consider for v2
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AI-01 | Claude API analyzes aggregated findings for business logic vulnerabilities (auth bypass, tenant isolation, IDOR) | AsyncAnthropic client + tool_use for structured JSON; system prompt with aipix-specific security concerns; component batching pattern |
| AI-02 | Claude generates code-level fix suggestions (before/after diffs) for each finding | tool_use JSON schema with `before`/`after`/`explanation` fields; nullable `fix_suggestion` with fallback `recommendation` |
| AI-03 | Claude correlates findings across tools to identify compound risks | Final cross-component API call; dedicated `compound_risks` + join table; severity assigned by Claude |
| AI-04 | AI analysis cost stays under $5 per release scan | `messages.count_tokens()` for pre-estimation; `response.usage` for actual tracking; severity-first batching with 80% budget cutoff; Sonnet 4.6 at $3/$15 per MTok |
| AI-05 | Scanner functions correctly when Claude API is unavailable (graceful degradation) | try/except around AI module; null AI fields; `ai_skipped` flag + reason on scan result |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | 0.86.0 | Anthropic Claude API client | Official SDK, async support, built-in token counting, typed responses |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | (already installed) | JSON schema for AI response validation | Validate Claude's structured responses before storing |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| anthropic SDK count_tokens | tiktoken character heuristic | SDK count_tokens is free, accurate, and GA -- no reason to use heuristics |
| tool_use for structured output | Parse free-text JSON from content | tool_use guarantees JSON schema conformance, avoids regex/parsing errors |

**Installation:**
```bash
pip install "anthropic>=0.86.0"
```

Add to pyproject.toml dependencies:
```
"anthropic>=0.86.0",
```

**Version verification:** `anthropic` 0.86.0 confirmed via `pip index versions anthropic` on 2026-03-19.

## Architecture Patterns

### Recommended Project Structure
```
src/scanner/
├── ai/
│   ├── __init__.py
│   ├── analyzer.py          # Main AIAnalyzer class (batch orchestration, budget tracking)
│   ├── prompts.py           # System prompt templates and component context mapping
│   ├── schemas.py           # Pydantic models for AI response validation
│   └── cost.py              # Cost calculation helpers (tokens -> USD)
├── models/
│   ├── compound_risk.py     # CompoundRisk ORM model + join table
│   └── ...existing...
├── schemas/
│   ├── compound_risk.py     # CompoundRiskSchema pydantic model
│   └── ...existing...
└── ...existing...
```

### Pattern 1: AsyncAnthropic Client with Tool Use
**What:** Use tool_use to force Claude to return structured JSON conforming to a defined schema.
**When to use:** Every API call where structured data is needed (all calls in this phase).
**Example:**
```python
# Source: https://platform.claude.com/docs/en/api/messages
from anthropic import AsyncAnthropic

client = AsyncAnthropic(api_key=settings.claude_api_key)

# Define the tool schema for structured output
analysis_tool = {
    "name": "security_analysis",
    "description": "Provide structured security analysis of findings",
    "input_schema": {
        "type": "object",
        "properties": {
            "findings_analysis": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "fingerprint": {"type": "string"},
                        "business_logic_risk": {"type": "string"},
                        "risk_category": {
                            "type": "string",
                            "enum": ["auth_bypass", "tenant_isolation", "idor",
                                     "memory_safety", "secret_exposure", "k8s_misconfig",
                                     "webhook_validation", "other"]
                        },
                        "fix_suggestion": {
                            "type": ["object", "null"],
                            "properties": {
                                "before": {"type": "string"},
                                "after": {"type": "string"},
                                "explanation": {"type": "string"}
                            }
                        },
                        "recommendation": {"type": ["string", "null"]}
                    },
                    "required": ["fingerprint", "business_logic_risk", "risk_category"]
                }
            }
        },
        "required": ["findings_analysis"]
    }
}

response = await client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    system=system_prompt,
    tools=[analysis_tool],
    tool_choice={"type": "tool", "name": "security_analysis"},
    messages=[{"role": "user", "content": user_prompt}],
)

# Extract structured JSON from tool_use block
for block in response.content:
    if block.type == "tool_use":
        analysis_data = block.input  # Already a dict
        break

# Track cost from response
input_tokens = response.usage.input_tokens
output_tokens = response.usage.output_tokens
```

### Pattern 2: Token Pre-Estimation with Budget Control
**What:** Use the free `count_tokens` endpoint to estimate batch cost before sending.
**When to use:** Before each batch API call to enforce budget limits.
**Example:**
```python
# Source: https://platform.claude.com/docs/en/build-with-claude/token-counting
# count_tokens is GA (no beta flag needed) and free
token_count = await client.messages.count_tokens(
    model="claude-sonnet-4-6",
    system=system_prompt,
    tools=[analysis_tool],
    messages=[{"role": "user", "content": batch_prompt}],
)
estimated_input_tokens = token_count.input_tokens

# Estimate cost: input $3/MTok + output ~$15/MTok
# Assume output ~= input * 0.3 (conservative for structured responses)
estimated_output_tokens = int(estimated_input_tokens * 0.3)
estimated_cost = (
    estimated_input_tokens * 3.0 / 1_000_000
    + estimated_output_tokens * 15.0 / 1_000_000
)
```

### Pattern 3: Component Batching with Severity Priority
**What:** Group findings by top-level directory, sort batches by max severity, process in priority order.
**When to use:** Core orchestration loop in AIAnalyzer.
**Example:**
```python
from collections import defaultdict
from scanner.schemas.severity import Severity

def group_by_component(findings: list[FindingSchema]) -> dict[str, list[FindingSchema]]:
    """Group findings by top-level directory (component)."""
    groups: dict[str, list[FindingSchema]] = defaultdict(list)
    for f in findings:
        component = f.file_path.split("/")[0] if "/" in f.file_path else "root"
        groups[component].append(f)
    return dict(groups)

def sort_batches_by_severity(
    batches: dict[str, list[FindingSchema]],
) -> list[tuple[str, list[FindingSchema]]]:
    """Sort component batches by max finding severity (highest first)."""
    def max_severity(findings: list[FindingSchema]) -> int:
        return max(f.severity.value for f in findings)
    return sorted(batches.items(), key=lambda x: max_severity(x[1]), reverse=True)
```

### Pattern 4: Graceful Degradation
**What:** Wrap entire AI analysis in try/except, return unmodified findings on failure.
**When to use:** Top-level AI integration in orchestrator.
**Example:**
```python
async def enrich_with_ai(
    findings: list[FindingSchema],
    settings: ScannerSettings,
) -> tuple[list[FindingSchema], list[CompoundRiskSchema], AIAnalysisResult]:
    """Enrich findings with AI analysis. Returns originals on failure."""
    result = AIAnalysisResult(skipped=False, skip_reason=None, cost_usd=0.0)

    if not settings.claude_api_key:
        result.skipped = True
        result.skip_reason = "Claude API key not configured"
        return findings, [], result

    try:
        analyzer = AIAnalyzer(settings)
        enriched, compound_risks, cost = await analyzer.analyze(findings)
        result.cost_usd = cost
        return enriched, compound_risks, result
    except Exception as exc:
        result.skipped = True
        result.skip_reason = f"AI analysis failed: {exc}"
        return findings, [], result
```

### Anti-Patterns to Avoid
- **Retry loops for API failures:** Context says "No retry loop -- single attempt per batch, fail fast." Only exception: rate limit (429) where a single short backoff is acceptable per Claude's Discretion.
- **Sending Low/Info findings to AI:** Budget waste. Context explicitly says skip Low/Info.
- **Free-form markdown responses from Claude:** Always use tool_use for structured JSON. Parsing markdown is fragile.
- **Estimating tokens with character count heuristics:** The `count_tokens` endpoint is free and accurate. Use it.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token counting | Character-based estimation | `client.messages.count_tokens()` | Free GA endpoint, matches billing accuracy |
| JSON schema enforcement | Post-hoc regex parsing of Claude's text | tool_use with `input_schema` | SDK handles schema validation, guaranteed structure |
| Cost calculation | Manual price lookup tables | Constants derived from official pricing + `response.usage` | Pricing is simple: $3/MTok input, $15/MTok output for Sonnet 4.6 |
| HTTP client for Anthropic API | Raw httpx calls | `anthropic.AsyncAnthropic` | SDK handles auth, retries, error types, response typing |

**Key insight:** The Anthropic SDK handles all the hard parts (auth, typed responses, token counting, error classification). The custom code should focus on batching logic, prompt engineering, and budget enforcement.

## Common Pitfalls

### Pitfall 1: Tool Use Response Parsing
**What goes wrong:** Assuming `response.content[0]` is always the tool_use block.
**Why it happens:** Claude may prepend a text block before the tool_use block, even with `tool_choice={"type": "tool"}`.
**How to avoid:** Always iterate `response.content` and find the block with `type == "tool_use"`.
**Warning signs:** `AttributeError` on `.input` when accessing a TextBlock.

### Pitfall 2: Budget Overshoot from Output Tokens
**What goes wrong:** Pre-estimation only counts input tokens, but output tokens cost 5x more ($15 vs $3 per MTok).
**Why it happens:** `count_tokens` returns input token count only. Output tokens are unknown until response arrives.
**How to avoid:** Use a conservative output multiplier (e.g., 0.3x input for structured responses) in budget estimation. Track actual cost after each call and adjust remaining budget.
**Warning signs:** Actual cost exceeds estimate by >50%.

### Pitfall 3: Large Batches Hitting Context Window
**What goes wrong:** A component with hundreds of findings creates a prompt exceeding the model's practical limits.
**Why it happens:** Some components (e.g., a large PHP VMS codebase) may have many findings.
**How to avoid:** Set a per-batch max finding count (e.g., 50). If a component exceeds this, split into sub-batches sorted by severity.
**Warning signs:** `count_tokens` returns >100K tokens for a single batch.

### Pitfall 4: SQLite Schema Migration
**What goes wrong:** Adding new columns/tables without migration path breaks existing databases.
**Why it happens:** Phase 1/2 used `Base.metadata.create_all` which only creates missing tables, not missing columns.
**How to avoid:** For new tables (`compound_risks`, `compound_risk_findings`), `create_all` works fine. For new columns on existing tables (`scans.ai_cost_usd`), use `ALTER TABLE` via Alembic or a manual migration check.
**Warning signs:** `OperationalError: no such column` on existing databases.

### Pitfall 5: API Key Missing vs API Unavailable
**What goes wrong:** Treating missing API key the same as API being down.
**Why it happens:** Both result in "no AI enrichment" but the root cause is different.
**How to avoid:** Check for empty `claude_api_key` before attempting API call. Log distinct messages: "API key not configured" vs "API call failed: [error]".
**Warning signs:** Confusing error messages in scan results.

## Code Examples

### AIAnalyzer Main Loop
```python
# Verified pattern combining official SDK docs
class AIAnalyzer:
    # Sonnet 4.6 pricing (per million tokens)
    INPUT_PRICE_PER_MTOK = 3.0
    OUTPUT_PRICE_PER_MTOK = 15.0
    OUTPUT_ESTIMATE_RATIO = 0.3  # Conservative output/input ratio
    BUDGET_CUTOFF = 0.80  # Stop at 80% of budget

    def __init__(self, settings: ScannerSettings):
        self.client = AsyncAnthropic(api_key=settings.claude_api_key)
        self.max_cost = settings.ai.max_cost_per_scan  # From config
        self.spent = 0.0
        self.analyzed_components: list[str] = []
        self.skipped_components: list[str] = []

    def _estimate_cost(self, input_tokens: int) -> float:
        est_output = int(input_tokens * self.OUTPUT_ESTIMATE_RATIO)
        return (
            input_tokens * self.INPUT_PRICE_PER_MTOK / 1_000_000
            + est_output * self.OUTPUT_PRICE_PER_MTOK / 1_000_000
        )

    def _actual_cost(self, usage) -> float:
        return (
            usage.input_tokens * self.INPUT_PRICE_PER_MTOK / 1_000_000
            + usage.output_tokens * self.OUTPUT_PRICE_PER_MTOK / 1_000_000
        )

    async def analyze(
        self, findings: list[FindingSchema]
    ) -> tuple[list[FindingSchema], list[CompoundRiskSchema], float]:
        # 1. Filter: only Critical/High/Medium (skip Low/Info)
        eligible = [f for f in findings if f.severity >= Severity.MEDIUM]
        if not eligible:
            return findings, [], 0.0

        # 2. Group by component, sort by severity
        batches = group_by_component(eligible)
        sorted_batches = sort_batches_by_severity(batches)

        # 3. Process batches within budget
        component_summaries = {}
        for component, batch_findings in sorted_batches:
            if self.spent >= self.max_cost * self.BUDGET_CUTOFF:
                self.skipped_components.append(component)
                continue

            # Pre-estimate
            prompt = build_component_prompt(component, batch_findings)
            token_count = await self.client.messages.count_tokens(
                model="claude-sonnet-4-6",
                system=build_system_prompt(component),
                tools=[ANALYSIS_TOOL],
                messages=[{"role": "user", "content": prompt}],
            )
            est_cost = self._estimate_cost(token_count.input_tokens)
            if self.spent + est_cost > self.max_cost * self.BUDGET_CUTOFF:
                self.skipped_components.append(component)
                continue

            # Call Claude
            response = await self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=build_system_prompt(component),
                tools=[ANALYSIS_TOOL],
                tool_choice={"type": "tool", "name": "security_analysis"},
                messages=[{"role": "user", "content": prompt}],
            )
            self.spent += self._actual_cost(response.usage)
            self.analyzed_components.append(component)

            # Parse and apply results
            # ... (extract tool_use block, update findings)

        # 4. Cross-component correlation call (if budget allows)
        if component_summaries and self.spent < self.max_cost * self.BUDGET_CUTOFF:
            compound_risks = await self._correlate(component_summaries)
        else:
            compound_risks = []

        return findings, compound_risks, self.spent
```

### Config Extension Pattern
```python
# Follows existing ScannerSettings pattern in config.py
class AIConfig(BaseModel):
    """AI analysis configuration."""
    max_cost_per_scan: float = 5.0
    model: str = "claude-sonnet-4-6"
    max_findings_per_batch: int = 50
    max_tokens_per_response: int = 4096

# Add to ScannerSettings:
class ScannerSettings(BaseSettings):
    # ... existing fields ...
    ai: AIConfig = AIConfig()
```

### Compound Risk DB Models
```python
# New tables for cross-tool correlation
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Table
from scanner.models.base import Base

# Join table
compound_risk_findings = Table(
    "compound_risk_findings",
    Base.metadata,
    Column("compound_risk_id", Integer, ForeignKey("compound_risks.id"), primary_key=True),
    Column("finding_fingerprint", String(64), nullable=False, primary_key=True),
)

class CompoundRisk(Base):
    __tablename__ = "compound_risks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(Integer, nullable=False)  # Maps to Severity IntEnum
    risk_category = Column(String(100), nullable=True)
    recommendation = Column(Text, nullable=True)

    scan = relationship("ScanResult", back_populates="compound_risks")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `client.beta.messages.count_tokens()` | `client.messages.count_tokens()` | SDK ~0.45+ (GA) | No beta flag needed, stable API |
| Character heuristic for token estimation | Official count_tokens endpoint | Nov 2024 | Free, accurate, matches billing |
| Free-text JSON in Claude responses | tool_use with input_schema | Always available | Guaranteed structured output |
| Long-context surcharge for >200K tokens | Flat rate at all context lengths | Mar 2026 | $3/MTok input regardless of prompt size |

**Deprecated/outdated:**
- `betas=["token-counting-2024-11-01"]`: No longer needed. `count_tokens` is GA on `client.messages`.
- `claude-3-5-sonnet-*` model strings: Superseded by `claude-sonnet-4-6`.

## Open Questions

1. **Rate limit handling strategy**
   - What we know: Context says "no retry loop" but Claude's Discretion includes "retry/backoff strategy for transient API errors (rate limits)"
   - What's unclear: Exact policy -- should a 429 get a single retry with backoff, or immediate failure?
   - Recommendation: Single retry with exponential backoff (e.g., 2s then 4s) for 429 only. All other errors fail immediately. This balances the "fail fast" directive with practical rate limit handling.

2. **Schema migration for existing databases**
   - What we know: `Base.metadata.create_all` creates new tables but not new columns on existing tables
   - What's unclear: Whether Alembic migrations are set up yet (alembic is in dependencies but may not be initialized)
   - Recommendation: For Phase 3, add `ai_cost_usd` column to `scans` table via a startup migration check (e.g., try ALTER TABLE, catch if column exists). New tables (`compound_risks`, `compound_risk_findings`) will be created automatically by `create_all`.

3. **Max findings per batch threshold**
   - What we know: Need to prevent oversized batches that hit context limits
   - What's unclear: Exact sweet spot for findings per batch
   - Recommendation: Default 50 findings per batch (configurable in AIConfig). Monitor actual token counts and adjust.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `python -m pytest tests/phase_03/ -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AI-01 | Claude analyzes findings for business logic vulns | unit (mocked API) | `python -m pytest tests/phase_03/test_analyzer.py::test_component_analysis -x` | No -- Wave 0 |
| AI-01 | System prompt includes aipix security concerns | unit | `python -m pytest tests/phase_03/test_prompts.py::test_system_prompt_content -x` | No -- Wave 0 |
| AI-02 | Fix suggestions have before/after/explanation | unit (mocked API) | `python -m pytest tests/phase_03/test_analyzer.py::test_fix_suggestion_format -x` | No -- Wave 0 |
| AI-02 | Null fix_suggestion with recommendation fallback | unit (mocked API) | `python -m pytest tests/phase_03/test_analyzer.py::test_null_fix_with_recommendation -x` | No -- Wave 0 |
| AI-03 | Cross-tool correlation produces compound risks | unit (mocked API) | `python -m pytest tests/phase_03/test_correlation.py::test_compound_risk_creation -x` | No -- Wave 0 |
| AI-03 | Compound risk severity affects quality gate | unit | `python -m pytest tests/phase_03/test_correlation.py::test_compound_risk_gate -x` | No -- Wave 0 |
| AI-04 | Budget tracking stays under limit | unit | `python -m pytest tests/phase_03/test_budget.py::test_budget_cutoff -x` | No -- Wave 0 |
| AI-04 | Severity-first batch ordering | unit | `python -m pytest tests/phase_03/test_budget.py::test_severity_priority_order -x` | No -- Wave 0 |
| AI-04 | Cost logged per scan | unit | `python -m pytest tests/phase_03/test_budget.py::test_cost_tracking -x` | No -- Wave 0 |
| AI-05 | Scan completes without AI when API unavailable | unit | `python -m pytest tests/phase_03/test_graceful_degradation.py::test_api_unavailable -x` | No -- Wave 0 |
| AI-05 | Scan completes when API key missing | unit | `python -m pytest tests/phase_03/test_graceful_degradation.py::test_no_api_key -x` | No -- Wave 0 |
| AI-05 | AI skip reason recorded in scan result | unit | `python -m pytest tests/phase_03/test_graceful_degradation.py::test_skip_reason_recorded -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/phase_03/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/phase_03/__init__.py` -- package init
- [ ] `tests/phase_03/conftest.py` -- shared fixtures (mock AsyncAnthropic, sample findings, mock responses)
- [ ] `tests/phase_03/test_analyzer.py` -- covers AI-01, AI-02 (component analysis, fix suggestions)
- [ ] `tests/phase_03/test_correlation.py` -- covers AI-03 (compound risks, gate impact)
- [ ] `tests/phase_03/test_budget.py` -- covers AI-04 (cost tracking, budget cutoff, priority ordering)
- [ ] `tests/phase_03/test_graceful_degradation.py` -- covers AI-05 (API unavailable, missing key, skip reason)
- [ ] `tests/phase_03/test_prompts.py` -- covers AI-01 (system prompt content, component context)
- [ ] `tests/phase_03/test_schemas.py` -- AI response schema validation

**Testing approach:** All tests use `unittest.mock.AsyncMock` to mock `AsyncAnthropic` (matching Phase 2 pattern). No real API calls in tests.

## Sources

### Primary (HIGH confidence)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) - v0.86.0 confirmed via pip index
- [Anthropic Messages API](https://platform.claude.com/docs/en/api/messages) - Response structure, tool_use pattern, usage fields
- [Anthropic Token Counting](https://platform.claude.com/docs/en/build-with-claude/token-counting) - GA endpoint, Python SDK usage, free pricing
- [Anthropic Pricing](https://platform.claude.com/docs/en/about-claude/pricing) - Sonnet 4.6: $3/$15 per MTok, flat rate at all context lengths

### Secondary (MEDIUM confidence)
- [Anthropic API Pricing Details](https://pricepertoken.com/pricing-page/model/anthropic-claude-sonnet-4.6) - Confirmed $3/$15 pricing, 1M context GA at standard pricing

### Tertiary (LOW confidence)
- Output token estimation ratio (0.3x input): Based on experience with structured tool_use responses. Should be validated against actual usage in first scans.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official SDK, verified version, confirmed pricing from official docs
- Architecture: HIGH - Patterns derived from official SDK docs and existing codebase patterns
- Pitfalls: MEDIUM - Based on SDK documentation and common integration patterns; some (like output ratio) need runtime validation

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (stable SDK, pricing may change)
