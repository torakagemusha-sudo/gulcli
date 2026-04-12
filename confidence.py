"""
Confidence Lattice - GUL v2.1

Bounded confidence values in [0,1] with algebraic operations.
Mirrors the GUL Lean specification for uncertainty handling.

Mathematical Foundation:
    - Confidence forms a bounded lattice with 0 (bottom) and 1 (top)
    - Operations: union (max), intersection (min), sequential (product), parallel (independence)
    - Complement: 1 - c
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Confidence:
    """
    Bounded confidence value in [0,1] - mirrors GUL Lean spec.

    Immutable value type with ordering based on confidence level.

    Attributes:
        value: Float in [0.0, 1.0] representing confidence level

    Examples:
        >>> c = Confidence(0.8)
        >>> c.value
        0.8
        >>> Confidence.zero()
        Confidence(value=0.0)
        >>> Confidence.one()
        Confidence(value=1.0)
    """

    value: float

    def __post_init__(self):
        if not (0.0 <= self.value <= 1.0):
            raise ValueError(f"Confidence must be in [0,1], got {self.value}")

    @classmethod
    def zero(cls) -> Confidence:
        """Bottom of confidence lattice (no confidence)."""
        return cls(0.0)

    @classmethod
    def one(cls) -> Confidence:
        """Top of confidence lattice (full confidence)."""
        return cls(1.0)

    @classmethod
    def from_probability(cls, p: float) -> Confidence:
        """Create confidence from probability, clamping to [0,1]."""
        return cls(max(0.0, min(1.0, p)))

    def complement(self) -> Confidence:
        """Logical complement: 1 - c."""
        return Confidence(1.0 - self.value)

    def is_certain(self, threshold: float = 1.0) -> bool:
        """Check if confidence meets certainty threshold."""
        return self.value >= threshold

    def is_uncertain(self, threshold: float = 0.5) -> bool:
        """Check if confidence is below uncertainty threshold."""
        return self.value < threshold

    def __repr__(self) -> str:
        return f"Confidence({self.value:.4f})"


class ConfidenceOps:
    """
    Combination operations from Uncertainty.lean.

    Provides algebraic operations for combining confidence values
    under different composition semantics.
    """

    @staticmethod
    def combine_union(c1: Confidence, c2: Confidence) -> Confidence:
        """
        Optimistic combination: max(c1, c2).

        Use when either source of evidence is sufficient.
        Corresponds to logical OR semantics.

        Args:
            c1: First confidence
            c2: Second confidence

        Returns:
            Maximum of the two confidences
        """
        return Confidence(max(c1.value, c2.value))

    @staticmethod
    def combine_intersection(c1: Confidence, c2: Confidence) -> Confidence:
        """
        Pessimistic combination: min(c1, c2).

        Use when both sources of evidence are required.
        Corresponds to logical AND semantics.

        Args:
            c1: First confidence
            c2: Second confidence

        Returns:
            Minimum of the two confidences
        """
        return Confidence(min(c1.value, c2.value))

    @staticmethod
    def combine_sequential(c1: Confidence, c2: Confidence) -> Confidence:
        """
        Sequential chain of reasoning: c1 * c2.

        Use for dependent evidence where uncertainty compounds.
        Models causal chains and transitive inference.

        Args:
            c1: First confidence
            c2: Second confidence

        Returns:
            Product of the two confidences
        """
        return Confidence(c1.value * c2.value)

    @staticmethod
    def combine_parallel(c1: Confidence, c2: Confidence) -> Confidence:
        """
        Independent evidence combination: c1 + c2 - c1*c2.

        Use for independent sources that reinforce each other.
        Based on probability of at least one being correct.

        Args:
            c1: First confidence
            c2: Second confidence

        Returns:
            Combined confidence from independent sources
        """
        return Confidence(c1.value + c2.value - c1.value * c2.value)

    @staticmethod
    def weighted_average(
        confidences: list[Confidence],
        weights: list[float] | None = None,
    ) -> Confidence:
        """
        Weighted average of multiple confidences.

        Args:
            confidences: List of confidence values
            weights: Optional weights (defaults to uniform)

        Returns:
            Weighted average confidence
        """
        if not confidences:
            return Confidence.one()

        if weights is None:
            weights = [1.0] * len(confidences)

        if len(weights) != len(confidences):
            raise ValueError("Weights must match number of confidences")

        total_weight = sum(weights)
        if total_weight == 0:
            return Confidence.one()

        weighted_sum = sum(c.value * w for c, w in zip(confidences, weights))
        return Confidence(weighted_sum / total_weight)

    @staticmethod
    def aggregate(
        confidences: list[Confidence],
        method: str = "min",
    ) -> Confidence:
        """
        Aggregate multiple confidences using specified method.

        Args:
            confidences: List of confidence values
            method: One of 'min', 'max', 'product', 'parallel', 'average'

        Returns:
            Aggregated confidence
        """
        if not confidences:
            return Confidence.one()

        if method == "min":
            return Confidence(min(c.value for c in confidences))
        elif method == "max":
            return Confidence(max(c.value for c in confidences))
        elif method == "product":
            result = Confidence.one()
            for c in confidences:
                result = ConfidenceOps.combine_sequential(result, c)
            return result
        elif method == "parallel":
            result = Confidence.zero()
            for c in confidences:
                result = ConfidenceOps.combine_parallel(result, c)
            return result
        elif method == "average":
            return ConfidenceOps.weighted_average(confidences)
        else:
            raise ValueError(f"Unknown aggregation method: {method}")
