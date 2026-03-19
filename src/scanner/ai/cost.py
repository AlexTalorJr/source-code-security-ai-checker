"""Token-to-USD cost calculation for AI analysis."""

INPUT_PRICE_PER_MTOK: float = 3.0
OUTPUT_PRICE_PER_MTOK: float = 15.0
OUTPUT_ESTIMATE_RATIO: float = 0.3
BUDGET_CUTOFF: float = 0.80


def estimate_cost(input_tokens: int) -> float:
    """Estimate total cost for a batch based on input token count.

    Estimates output tokens as input_tokens * OUTPUT_ESTIMATE_RATIO.

    Args:
        input_tokens: Number of input tokens.

    Returns:
        Estimated cost in USD.
    """
    estimated_output = input_tokens * OUTPUT_ESTIMATE_RATIO
    return (
        input_tokens * INPUT_PRICE_PER_MTOK / 1e6
        + estimated_output * OUTPUT_PRICE_PER_MTOK / 1e6
    )


def actual_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculate exact cost from known token counts.

    Args:
        input_tokens: Number of input tokens used.
        output_tokens: Number of output tokens used.

    Returns:
        Actual cost in USD.
    """
    return (
        input_tokens * INPUT_PRICE_PER_MTOK / 1e6
        + output_tokens * OUTPUT_PRICE_PER_MTOK / 1e6
    )


def is_within_budget(
    spent: float,
    estimated_next: float,
    max_cost: float,
    cutoff: float = BUDGET_CUTOFF,
) -> bool:
    """Check if next batch fits within remaining budget.

    Args:
        spent: Total USD already spent this scan.
        estimated_next: Estimated cost of next batch.
        max_cost: Maximum allowed cost per scan.
        cutoff: Budget cutoff ratio (default 0.80).

    Returns:
        True if spent + estimated_next <= max_cost * cutoff.
    """
    return spent + estimated_next <= max_cost * cutoff
