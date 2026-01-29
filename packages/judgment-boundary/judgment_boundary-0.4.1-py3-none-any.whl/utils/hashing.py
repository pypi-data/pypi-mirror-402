"""
Hashing utilities for signature generation.
판단 추적을 위한 서명 생성.
"""

import hashlib
import json
from typing import Any


def generate_prompt_signature(prompt: str, normalize: bool = True) -> str:
    """
    프롬프트의 고유 서명 생성.

    Args:
        prompt: 입력 프롬프트
        normalize: 공백 정규화 여부

    Returns:
        SHA-256 해시 서명
    """
    if normalize:
        # 공백 정규화 (의미는 같지만 공백이 다른 경우 동일 처리)
        prompt = " ".join(prompt.split())

    return hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:16]


def generate_trace_signature(prompt: str, model_output: str, timestamp: str) -> str:
    """
    전체 실행의 추적 가능한 서명 생성.

    Args:
        prompt: 입력 프롬프트
        model_output: 모델 출력
        timestamp: 타임스탬프

    Returns:
        SHA-256 해시 서명
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
    판단 결정의 고유 서명 생성.

    Args:
        prompt_sig: 프롬프트 서명
        decision: 판단 결정
        reason_slots: 이유 슬롯들

    Returns:
        SHA-256 해시 서명
    """
    data = {
        "prompt": prompt_sig,
        "decision": decision,
        "reasons": sorted(reason_slots)
    }
    content = json.dumps(data, sort_keys=True)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
