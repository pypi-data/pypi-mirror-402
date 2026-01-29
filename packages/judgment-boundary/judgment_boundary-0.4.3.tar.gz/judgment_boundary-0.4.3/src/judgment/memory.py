"""
Judgment Memory Store
Append-only store for accumulating judgment patterns.

This is not a log, but a learning state store.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import json
from datetime import datetime
from collections import defaultdict

from models.schemas import (
    JudgmentMemoryEntry,
    JudgmentDecision,
    ReasonSlot,
    DomainTag
)


class JudgmentMemoryStore:
    """
    Judgment Memory Store.

    Rules:
    - Append-only (no modifications)
    - Store all judgments
    - Separate from model ID
    """

    def __init__(self, storage_path: str = "./judgment_memory.jsonl"):
        """
        Args:
            storage_path: Storage file path (JSONL format)
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage()

    def _ensure_storage(self):
        """Check/create storage file"""
        if not self.storage_path.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.touch()

    def append(self, entry: JudgmentMemoryEntry) -> bool:
        """
        Add judgment entry (append-only).

        Args:
            entry: Judgment entry to store

        Returns:
            Success status
        """
        try:
            with open(self.storage_path, 'a', encoding='utf-8') as f:
                # JSONL format: each line is a JSON object
                json_str = entry.model_dump_json()
                f.write(json_str + '\n')
            return True
        except Exception as e:
            print(f"Error appending to memory store: {e}")
            return False

    def query_by_prompt_signature(
        self,
        prompt_signature: str
    ) -> List[JudgmentMemoryEntry]:
        """
        Query by prompt signature.

        Args:
            prompt_signature: Prompt signature to query

        Returns:
            Matching entries
        """
        results = []
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry_dict = json.loads(line)
                        if entry_dict.get('prompt_signature') == prompt_signature:
                            results.append(JudgmentMemoryEntry(**entry_dict))
        except Exception as e:
            print(f"Error querying memory store: {e}")

        return results

    def query_by_domain(
        self,
        domain_tag: DomainTag,
        limit: Optional[int] = None
    ) -> List[JudgmentMemoryEntry]:
        """
        Query by domain.

        Args:
            domain_tag: Domain tag
            limit: Maximum number of entries to return

        Returns:
            Matching entries
        """
        results = []
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry_dict = json.loads(line)
                        if entry_dict.get('domain_tag') == domain_tag.value:
                            results.append(JudgmentMemoryEntry(**entry_dict))
                            if limit and len(results) >= limit:
                                break
        except Exception as e:
            print(f"Error querying memory store: {e}")

        return results

    def get_decision_stats(
        self,
        prompt_signature: Optional[str] = None,
        domain_tag: Optional[DomainTag] = None
    ) -> Dict[str, Any]:
        """
        Query judgment statistics.

        Args:
            prompt_signature: Filter by specific prompt (optional)
            domain_tag: Filter by specific domain (optional)

        Returns:
            Statistics information
        """
        stats = {
            "total_count": 0,
            "decision_counts": defaultdict(int),
            "reason_slot_counts": defaultdict(int),
            "avg_confidence": 0.0,
            "confidence_sum": 0.0
        }

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry_dict = json.loads(line)

                        # Apply filters
                        if prompt_signature and entry_dict.get('prompt_signature') != prompt_signature:
                            continue
                        if domain_tag and entry_dict.get('domain_tag') != domain_tag.value:
                            continue

                        # Collect statistics
                        stats["total_count"] += 1
                        stats["decision_counts"][entry_dict.get('decision')] += 1
                        stats["confidence_sum"] += entry_dict.get('confidence', 0.0)

                        for reason in entry_dict.get('reason_slots', []):
                            stats["reason_slot_counts"][reason] += 1

            # Calculate average
            if stats["total_count"] > 0:
                stats["avg_confidence"] = stats["confidence_sum"] / stats["total_count"]

            # Convert defaultdict to regular dict
            stats["decision_counts"] = dict(stats["decision_counts"])
            stats["reason_slot_counts"] = dict(stats["reason_slot_counts"])

        except Exception as e:
            print(f"Error getting stats: {e}")

        return stats

    def get_recent_entries(
        self,
        limit: int = 100
    ) -> List[JudgmentMemoryEntry]:
        """
        Query recent entries.

        Args:
            limit: Maximum number to return

        Returns:
            Recent entries
        """
        results = []
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Read from end
                for line in reversed(lines[-limit:]):
                    if line.strip():
                        entry_dict = json.loads(line)
                        results.append(JudgmentMemoryEntry(**entry_dict))
        except Exception as e:
            print(f"Error getting recent entries: {e}")

        return results

    def count_stop_decisions(
        self,
        prompt_signature: str
    ) -> int:
        """
        Count STOP decisions for specific prompt.

        Args:
            prompt_signature: Prompt signature

        Returns:
            Number of STOP decisions
        """
        count = 0
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry_dict = json.loads(line)
                        if (entry_dict.get('prompt_signature') == prompt_signature and
                            entry_dict.get('decision') == JudgmentDecision.STOP.value):
                            count += 1
        except Exception as e:
            print(f"Error counting STOP decisions: {e}")

        return count

    def get_domain_stop_ratio(
        self,
        domain_tag: DomainTag
    ) -> float:
        """
        Query STOP ratio for specific domain.

        Args:
            domain_tag: Domain tag

        Returns:
            STOP ratio (0.0 ~ 1.0)
        """
        stats = self.get_decision_stats(domain_tag=domain_tag)
        total = stats["total_count"]
        if total == 0:
            return 0.0

        stop_count = stats["decision_counts"].get(JudgmentDecision.STOP.value, 0)
        return stop_count / total
