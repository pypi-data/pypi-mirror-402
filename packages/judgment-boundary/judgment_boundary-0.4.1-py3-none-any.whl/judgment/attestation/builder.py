"""
Boundary Attestation Builder특정 시점의 조직 성격을 변경 불가능한 증명 객체로 생성.

Attestation ≠ Report
- Report: 설명 문서 (변경 가능)
- Attestation: 시점 봉인 증명 (변경 불가, 재현 가능)
"""

from typing import Dict, List, Optional
from datetime import datetime
import hashlib
import json

from models.schemas import (
    BoundaryAttestation,
    OrganizationProfile,
    JudgmentBoundaryProfile,
    BoundaryDeclarationEvent
)


class BoundaryAttestationBuilder:
    """
    조직 성격 증명 빌더.

    v0.4 핵심: 내부 완성된 성격 → 외부 제시 가능한 증명
    """

    def __init__(self, runtime_version: str = "v0.4"):
        """
        Args:
            runtime_version: Runtime 버전
        """
        self.runtime_version = runtime_version

    def build_attestation(
        self,
        organization_id: str,
        org_profile: OrganizationProfile,
        active_declarations: List[BoundaryDeclarationEvent],
        effective_at: Optional[datetime] = None
    ) -> BoundaryAttestation:
        """
        Attestation 생성.

        Args:
            organization_id: 조직 ID
            org_profile: 조직 프로필
            active_declarations: 활성 선언들
            effective_at: 유효 시점 (None이면 현재)

        Returns:
            BoundaryAttestation
        """
        if effective_at is None:
            effective_at = datetime.utcnow()

        # 1. 경계 요약 생성
        boundary_summary = self._generate_boundary_summary(
            org_profile, active_declarations
        )

        # 2. 해시 생성 (무결성 보장)
        profile_hash = self._hash_profile(org_profile)
        declarations_hash = self._hash_declarations(active_declarations)

        # 3. Attestation ID 생성
        attestation_id = self._generate_attestation_id(
            organization_id, effective_at
        )

        # 4. 도메인 목록
        domains_included = list(org_profile.domain_profiles.keys())

        return BoundaryAttestation(
            attestation_id=attestation_id,
            organization_id=organization_id,
            effective_at=effective_at,
            boundary_summary=boundary_summary,
            profile_hash=profile_hash,
            declarations_hash=declarations_hash,
            runtime_version=self.runtime_version,
            generation_method="deterministic",
            domains_included=domains_included,
            declarations_count=len(active_declarations),
            immutable=True
        )

    def _generate_boundary_summary(
        self,
        org_profile: OrganizationProfile,
        active_declarations: List[BoundaryDeclarationEvent]
    ) -> Dict[str, str]:
        """
        도메인별 경계 요약 생성.

        Args:
            org_profile: 조직 프로필
            active_declarations: 활성 선언들

        Returns:
            도메인별 요약
        """
        summary = {}

        # 선언 우선 (v0.3 우선순위 규칙)
        for decl in active_declarations:
            domain = decl.domain_tag.value
            summary[domain] = decl.declaration.value

        # 선언 없는 도메인은 프로필에서 가져옴
        for domain, profile in org_profile.domain_profiles.items():
            if domain not in summary:
                # 경계 강도를 요약으로 사용
                summary[domain] = profile.boundary_strength.value

        return summary

    def _hash_profile(self, org_profile: OrganizationProfile) -> str:
        """
        프로필 해시 생성 (무결성 보장).

        Args:
            org_profile: 조직 프로필

        Returns:
            SHA-256 해시
        """
        # 재현 가능하도록 정렬된 JSON
        profile_dict = org_profile.model_dump()
        json_str = json.dumps(profile_dict, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

    def _hash_declarations(
        self,
        declarations: List[BoundaryDeclarationEvent]
    ) -> str:
        """
        선언 이벤트 해시 생성.

        Args:
            declarations: 선언 이벤트들

        Returns:
            SHA-256 해시
        """
        if not declarations:
            return hashlib.sha256(b"").hexdigest()

        # 재현 가능하도록 정렬
        decls_sorted = sorted(
            [d.model_dump() for d in declarations],
            key=lambda x: x['event_id']
        )
        json_str = json.dumps(decls_sorted, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

    def _generate_attestation_id(
        self,
        organization_id: str,
        effective_at: datetime
    ) -> str:
        """
        Attestation ID 생성.

        Args:
            organization_id: 조직 ID
            effective_at: 유효 시점

        Returns:
            Attestation ID (e.g., ATT-2026-01-ABCD1234)
        """
        # 형식: ATT-YYYY-MM-{hash}
        year_month = effective_at.strftime("%Y-%m")

        # 조직 ID + 시점의 해시
        content = f"{organization_id}:{effective_at.isoformat()}"
        hash_suffix = hashlib.sha256(content.encode('utf-8')).hexdigest()[:8].upper()

        return f"ATT-{year_month}-{hash_suffix}"
