"""
Hashing utilities for signature generation.
Signature generation for judgment tracing.
"""

import hashlib
import json
from typing import Any


def generate_prompt_signature(prompt: str, normalize: bool = True) -> str:
    """
    Generate unique signature for prompt.

    Args:
        prompt: Input prompt
        normalize: Whether to normalize whitespace

    Returns:
        SHA-256 hash signature
    """
    if normalize:
        # Normalize whitespace (treat same meaning with different spacing equally)
        prompt = " ".join(prompt.split())

    return hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:16]


def generate_trace_signature(prompt: str, model_output: str, timestamp: str) -> str:
    """
    Generate traceable signature for entire execution.

    Args:
        prompt: Input prompt
        model_output: Model output
        timestamp: Timestamp

    Returns:
        SHA-256 hash signature
    """
    data = {
        "prompt": prompt,
        "output": model_output,
        "timestamp": timestamp
    }
    content = json.dumps(data, sort_keys=True)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:24]


def generate_decision_signature(
    prompt_sig: str,
    decision: str,
    reason_slots: list
) -> str:
    """
    Generate unique signature for judgment decision.

    Args:
        prompt_sig: Prompt signature
        decision: Judgment decision
        reason_slots: Reason slots

    Returns:
        SHA-256 hash signature
    """
    data = {
        "prompt": prompt_sig,
        "decision": decision,
        "reasons": sorted(reason_slots)
    }
    content = json.dumps(data, sort_keys=True)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
