"""
PUBLIC SDK MODULE — STABLE CONTRACT

This module enforces judgment boundaries.
It does not make decisions.
It does not learn.
It does not optimize.

This module provides boundary enforcement before execution.
Organizations use this to prove which decisions were never automated.
"""

from typing import Optional, List
from judgment.runtime import JudgmentRuntime as _InternalRuntime
from judgment_boundary.types import (
    Decision,
    BoundaryReason,
    DomainTag,
    OrganizationalProfile,
)


class JudgmentRuntime:
    """
    PUBLIC API — STABLE CONTRACT

    Judgment Runtime enforces organizational boundaries before execution.

    This class does NOT:
    - Make autonomous decisions
    - Learn from data
    - Optimize behavior
    - Modify AI models

    This class DOES:
    - Enforce STOP/HOLD/ALLOW/INDETERMINATE boundaries
    - Record judgment traces externally
    - Aggregate patterns into organizational profiles
    - Maintain accountability through declarations and overrides
    """

    def __init__(
        self,
        memory_store_path: str = "./judgment_memory.jsonl",
        enable_organizational_memory: bool = False,
        enable_adaptation: bool = False,
        enable_negative_proof: bool = False,
        profile_store_path: Optional[str] = None,
        organization_id: str = "default"
    ):
        """
        Initialize Judgment Runtime.

        Args:
            memory_store_path: Path to judgment trace storage (JSONL)
            enable_organizational_memory: Enable profile aggregation (v0.2)
            enable_adaptation: Enable pattern-based adaptation (v0.1)
            enable_negative_proof: Enable negative proof generation (v0.1)
            profile_store_path: Path to organizational profile storage (JSON)
            organization_id: Organization identifier
        """
        self._runtime = _InternalRuntime(
            memory_store_path=memory_store_path,
            enable_organizational_memory=enable_organizational_memory,
            enable_adaptation=enable_adaptation,
            enable_negative_proof=enable_negative_proof,
            profile_store_path=profile_store_path,
            organization_id=organization_id
        )

    def process(
        self,
        prompt: str,
        model_output: Optional[str] = None,
        rag_sources: Optional[List[str]] = None,
        domain_tag: DomainTag = DomainTag.GENERAL,
        assumption_mode: bool = False
    ):
        """
        Process a judgment boundary check.

        This method enforces organizational boundaries BEFORE execution.
        It does NOT generate responses or make decisions.

        Args:
            prompt: User input/question
            model_output: Model-generated response (optional)
            rag_sources: Evidence sources from RAG (optional)
            domain_tag: Domain classification
            assumption_mode: Whether unverified assumptions are allowed

        Returns:
            JudgmentResult with decision (STOP/HOLD/ALLOW/INDETERMINATE)
        """
        return self._runtime.process(
            prompt=prompt,
            model_output=model_output,
            rag_sources=rag_sources,
            domain_tag=domain_tag,
            assumption_mode=assumption_mode
        )

    def build_organizational_profile(self) -> OrganizationalProfile:
        """
        Build organizational profile from judgment traces.

        Aggregates patterns using:
        - Frequency counting (how often each decision occurred)
        - Repetition detection (consecutive patterns)
        - Temporal stability (consistency over time)

        NO machine learning. NO statistics. Deterministic counters only.

        Returns:
            OrganizationalProfile with boundary characteristics

        Raises:
            ValueError: If insufficient judgments (< 20 per domain)
        """
        return self._runtime.build_organizational_profile()

    def explain_organizational_character(
        self,
        domain: DomainTag,
        format: str = "paragraph"
    ) -> str:
        """
        Generate human-readable explanation of organizational character.

        Args:
            domain: Domain to explain
            format: Output format ("paragraph" | "bullet" | "formal")

        Returns:
            Human-readable explanation of boundary profile
        """
        return self._runtime.explain_organizational_character(domain, format)


# Public API surface
__all__ = ['JudgmentRuntime']
