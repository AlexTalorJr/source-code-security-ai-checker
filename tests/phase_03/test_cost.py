"""Tests for AI cost calculation module."""

from scanner.ai.cost import actual_cost, estimate_cost, is_within_budget


class TestEstimateCost:
    def test_1000_input_tokens(self):
        # input cost: 1000 * 3.0 / 1e6 = 0.003
        # estimated output: 1000 * 0.3 = 300
        # output cost: 300 * 15.0 / 1e6 = 0.0045
        # total: 0.003 + 0.0045 = 0.0075
        cost = estimate_cost(1000)
        expected = 1000 * 3.0 / 1e6 + 300 * 15.0 / 1e6
        assert abs(cost - expected) < 1e-10


class TestActualCost:
    def test_known_tokens(self):
        # input: 1000 * 3.0 / 1e6 = 0.003
        # output: 500 * 15.0 / 1e6 = 0.0075
        # total: 0.0105
        cost = actual_cost(input_tokens=1000, output_tokens=500)
        expected = 1000 * 3.0 / 1e6 + 500 * 15.0 / 1e6
        assert abs(cost - expected) < 1e-10


class TestIsWithinBudget:
    def test_over_budget(self):
        # spent=4.0, estimated_next=0.5, max=5.0, cutoff=0.8
        # 4.0 + 0.5 = 4.5 > 5.0 * 0.8 = 4.0 -> False
        assert is_within_budget(spent=4.0, estimated_next=0.5, max_cost=5.0, cutoff=0.8) is False

    def test_within_budget(self):
        # spent=2.0, estimated_next=0.5, max=5.0, cutoff=0.8
        # 2.0 + 0.5 = 2.5 <= 5.0 * 0.8 = 4.0 -> True
        assert is_within_budget(spent=2.0, estimated_next=0.5, max_cost=5.0, cutoff=0.8) is True
