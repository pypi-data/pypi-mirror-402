"""
Judgment Runtime - External Accumulation Loop
Model-Agnostic Judgment System

v0.1: External Accumulation Loop
v0.2: Organizational Memory Layer
v0.3: Boundary Governance & Override Layer
"""

from .runtime import JudgmentRuntime
from .decision import JudgmentDecisionModule
from .negative_proof import NegativeProofGenerator
from .memory import JudgmentMemoryStore
from .adaptation import OnlineAdaptationEngine

# v0.2: Organizational Memory Layer
try:
    from .aggregator import JudgmentMemoryAggregator
    from .profile_store import OrganizationProfileStore

    # v0.3: Boundary Governance & Override Layer
    from .explainer import BoundaryProfileExplainer
    from .declaration import BoundaryDeclarationStore
    from .override import HumanOverrideStore
    from .diff import BoundaryDiffEngine

    __all__ = [
        # v0.1
        "JudgmentRuntime",
        "JudgmentDecisionModule",
        "NegativeProofGenerator",
        "JudgmentMemoryStore",
        "OnlineAdaptationEngine",
        # v0.2
        "JudgmentMemoryAggregator",
        "OrganizationProfileStore",
        # v0.3
        "BoundaryProfileExplainer",
        "BoundaryDeclarationStore",
        "HumanOverrideStore",
        "BoundaryDiffEngine",
    ]
except ImportError:
    __all__ = [
        "JudgmentRuntime",
        "JudgmentDecisionModule",
        "NegativeProofGenerator",
        "JudgmentMemoryStore",
        "OnlineAdaptationEngine",
    ]
