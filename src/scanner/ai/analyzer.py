"""AI-powered security finding analyzer using Claude API."""

from collections import defaultdict

from anthropic import AsyncAnthropic

from scanner.ai.cost import actual_cost, estimate_cost, is_within_budget
from scanner.ai.prompts import (
    ANALYSIS_TOOL,
    CORRELATION_TOOL,
    build_component_prompt,
    build_correlation_prompt,
    build_system_prompt,
)
from scanner.ai.schemas import (
    ComponentAnalysisResponse,
    CorrelationResponse,
    FindingAnalysis,
)
from scanner.config import ScannerSettings
from scanner.schemas.compound_risk import CompoundRiskSchema
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity


def group_by_component(
    findings: list[FindingSchema],
) -> dict[str, list[FindingSchema]]:
    """Group findings by top-level directory. Files without '/' go to 'root'."""
    groups: dict[str, list[FindingSchema]] = defaultdict(list)
    for f in findings:
        if "/" in f.file_path:
            component = f.file_path.split("/")[0]
        else:
            component = "root"
        groups[component].append(f)
    return dict(groups)


def sort_batches_by_severity(
    batches: dict[str, list[FindingSchema]],
) -> list[tuple[str, list[FindingSchema]]]:
    """Sort component batches by max finding severity (highest first)."""
    return sorted(
        batches.items(),
        key=lambda item: max(f.severity.value for f in item[1]),
        reverse=True,
    )


class AIAnalyzer:
    """Orchestrates Claude API calls for security finding analysis.

    Processes findings in component batches ordered by severity,
    enforces token budget, and runs cross-component correlation.
    """

    def __init__(self, settings: ScannerSettings) -> None:
        self.client = AsyncAnthropic(api_key=settings.claude_api_key)
        self.model = settings.ai.model
        self.max_cost = settings.ai.max_cost_per_scan
        self.max_findings_per_batch = settings.ai.max_findings_per_batch
        self.max_tokens = settings.ai.max_tokens_per_response
        self.spent: float = 0.0
        self.analyzed_components: list[str] = []
        self.skipped_components: list[str] = []

    async def analyze(
        self, findings: list[FindingSchema]
    ) -> tuple[list[FindingSchema], list[CompoundRiskSchema], float]:
        """Analyze findings with Claude API, applying AI enrichment.

        Args:
            findings: List of deduplicated security findings.

        Returns:
            Tuple of (enriched findings, compound risks, total cost USD).
        """
        if not findings:
            return findings, [], 0.0

        # Filter: only Critical/High/Medium worth API cost
        eligible = [f for f in findings if f.severity >= Severity.MEDIUM]
        if not eligible:
            return findings, [], 0.0

        # Group by component, sort by severity
        batches = group_by_component(eligible)
        sorted_batches = sort_batches_by_severity(batches)

        # Process each component batch
        component_summaries: dict[str, list[dict]] = {}
        findings_by_fp = {f.fingerprint: f for f in findings}

        for component, batch_findings in sorted_batches:
            sub_batches = self._split_batch(batch_findings)
            component_analyses: list[FindingAnalysis] = []

            for sub_batch in sub_batches:
                result = await self._analyze_component(component, sub_batch)
                if result is None:
                    self.skipped_components.append(component)
                    break
                component_analyses.extend(result)

                # Apply to findings
                for analysis in result:
                    finding = findings_by_fp.get(analysis.fingerprint)
                    if finding:
                        finding.ai_analysis = analysis.business_logic_risk
                        if analysis.fix_suggestion:
                            finding.ai_fix_suggestion = (
                                analysis.fix_suggestion.model_dump_json()
                            )
                        elif analysis.recommendation:
                            finding.ai_analysis = (
                                f"{analysis.business_logic_risk}\n\n"
                                f"Recommendation: {analysis.recommendation}"
                            )
            else:
                # Only add to analyzed if all sub-batches completed
                self.analyzed_components.append(component)
                component_summaries[component] = [
                    a.model_dump() for a in component_analyses
                ]

        # Cross-component correlation
        compound_risks: list[CompoundRiskSchema] = []
        if component_summaries and is_within_budget(
            self.spent, 0.5, self.max_cost
        ):
            compound_risks = await self._correlate(component_summaries)

        return findings, compound_risks, self.spent

    def _split_batch(
        self, findings: list[FindingSchema]
    ) -> list[list[FindingSchema]]:
        """Split batch into sub-batches of max_findings_per_batch, sorted by severity desc."""
        sorted_findings = sorted(
            findings, key=lambda f: f.severity.value, reverse=True
        )
        return [
            sorted_findings[i : i + self.max_findings_per_batch]
            for i in range(0, len(sorted_findings), self.max_findings_per_batch)
        ]

    async def _analyze_component(
        self, component: str, findings: list[FindingSchema]
    ) -> list[FindingAnalysis] | None:
        """Analyze a single component batch. Returns None if budget exceeded."""
        system_prompt = build_system_prompt(component)
        user_prompt = build_component_prompt(component, findings)

        # Pre-estimate cost via count_tokens
        token_count = await self.client.messages.count_tokens(
            model=self.model,
            system=system_prompt,
            tools=[ANALYSIS_TOOL],
            messages=[{"role": "user", "content": user_prompt}],
        )
        est = estimate_cost(token_count.input_tokens)
        if not is_within_budget(self.spent, est, self.max_cost):
            return None

        # Call Claude
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            tools=[ANALYSIS_TOOL],
            tool_choice={"type": "tool", "name": "security_analysis"},
            messages=[{"role": "user", "content": user_prompt}],
        )
        self.spent += actual_cost(
            response.usage.input_tokens, response.usage.output_tokens
        )

        # Parse tool_use response (iterate, don't assume index 0)
        analysis_data = None
        for block in response.content:
            if block.type == "tool_use":
                analysis_data = block.input
                break
        if analysis_data is None:
            return []

        parsed = ComponentAnalysisResponse(**analysis_data)
        return parsed.findings_analysis

    async def _correlate(
        self, component_summaries: dict[str, list[dict]]
    ) -> list[CompoundRiskSchema]:
        """Run cross-component correlation call."""
        system_prompt = (
            "You are a security analyst performing cross-component "
            "risk correlation for the aipix VSaaS platform."
        )
        user_prompt = build_correlation_prompt(component_summaries)

        # Pre-estimate cost
        token_count = await self.client.messages.count_tokens(
            model=self.model,
            system=system_prompt,
            tools=[CORRELATION_TOOL],
            messages=[{"role": "user", "content": user_prompt}],
        )
        est = estimate_cost(token_count.input_tokens)
        if not is_within_budget(self.spent, est, self.max_cost):
            return []

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            tools=[CORRELATION_TOOL],
            tool_choice={
                "type": "tool",
                "name": "cross_component_correlation",
            },
            messages=[{"role": "user", "content": user_prompt}],
        )
        self.spent += actual_cost(
            response.usage.input_tokens, response.usage.output_tokens
        )

        corr_data = None
        for block in response.content:
            if block.type == "tool_use":
                corr_data = block.input
                break
        if corr_data is None:
            return []

        parsed = CorrelationResponse(**corr_data)
        return [
            CompoundRiskSchema(
                title=cr.title,
                description=cr.description,
                severity=(
                    Severity[cr.severity.upper()].value
                    if cr.severity.upper() in Severity.__members__
                    else Severity.MEDIUM.value
                ),
                risk_category=cr.risk_category,
                finding_fingerprints=cr.finding_fingerprints,
                recommendation=cr.recommendation,
            )
            for cr in parsed.compound_risks
        ]
