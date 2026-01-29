"""
Organization Profile Store
조직의 판단 성격(Profile)을 저장하고 조회하는 저장소.

판단 로그와 분리되어 독립적으로 설명 가능해야 한다.
"""

from typing import Optional, Dict
from pathlib import Path
import json
from datetime import datetime

from models.schemas import (
    OrganizationProfile,
    JudgmentBoundaryProfile,
    DomainTag
)


class OrganizationProfileStore:
    """
    조직 프로필 저장소.

    "이 조직은 이 지점에서 자동화를 허용하지 않는다"를
    로그가 아니라 구조로 저장한다.
    """

    def __init__(self, storage_path: str = "./organization_profile.json"):
        """
        Args:
            storage_path: 프로필 저장 경로 (JSON 형식)
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage()

    def _ensure_storage(self):
        """저장소 파일 확인/생성"""
        if not self.storage_path.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            # 빈 프로필 생성
            empty_profile = OrganizationProfile()
            self.save_profile(empty_profile)

    def save_profile(self, profile: OrganizationProfile) -> bool:
        """
        조직 프로필 저장.

        Args:
            profile: OrganizationProfile

        Returns:
            성공 여부
        """
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json_data = profile.model_dump_json(indent=2)
                f.write(json_data)
            return True
        except Exception as e:
            print(f"Error saving organization profile: {e}")
            return False

    def load_profile(
        self,
        organization_id: str = "default"
    ) -> Optional[OrganizationProfile]:
        """
        조직 프로필 로드.

        Args:
            organization_id: 조직 ID

        Returns:
            OrganizationProfile or None
        """
        try:
            if not self.storage_path.exists():
                return None

            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # organization_id 확인
            if data.get("organization_id") != organization_id:
                return None

            return OrganizationProfile(**data)
        except Exception as e:
            print(f"Error loading organization profile: {e}")
            return None

    def get_domain_profile(
        self,
        domain_tag: DomainTag,
        organization_id: str = "default"
    ) -> Optional[JudgmentBoundaryProfile]:
        """
        특정 도메인의 Boundary Profile 조회.

        Args:
            domain_tag: 도메인
            organization_id: 조직 ID

        Returns:
            JudgmentBoundaryProfile or None
        """
        profile = self.load_profile(organization_id)
        if not profile:
            return None

        domain_key = domain_tag.value
        if domain_key not in profile.domain_profiles:
            return None

        return profile.domain_profiles[domain_key]

    def update_domain_profile(
        self,
        domain_profile: JudgmentBoundaryProfile,
        organization_id: str = "default"
    ) -> bool:
        """
        특정 도메인의 프로필 업데이트.

        Args:
            domain_profile: JudgmentBoundaryProfile
            organization_id: 조직 ID

        Returns:
            성공 여부
        """
        # 기존 프로필 로드
        org_profile = self.load_profile(organization_id)
        if not org_profile:
            # 새로 생성
            org_profile = OrganizationProfile(organization_id=organization_id)

        # 도메인 프로필 업데이트
        domain_key = domain_profile.domain_tag.value
        org_profile.domain_profiles[domain_key] = domain_profile

        # 전체 판단 수 업데이트
        org_profile.total_judgments = sum(
            p.sample_count for p in org_profile.domain_profiles.values()
        )

        # 마지막 업데이트 시간
        org_profile.last_updated = datetime.utcnow()

        # 저장
        return self.save_profile(org_profile)

    def get_profile_summary(
        self,
        organization_id: str = "default"
    ) -> Dict:
        """
        조직 프로필 요약 조회.

        Args:
            organization_id: 조직 ID

        Returns:
            요약 정보
        """
        profile = self.load_profile(organization_id)
        if not profile:
            return {
                "organization_id": organization_id,
                "exists": False,
                "total_judgments": 0,
                "domains": []
            }

        return {
            "organization_id": profile.organization_id,
            "exists": True,
            "total_judgments": profile.total_judgments,
            "overall_boundary_strength": profile.overall_boundary_strength.value,
            "domains": [
                {
                    "domain": domain,
                    "boundary_strength": p.boundary_strength.value,
                    "dominant_decision": p.dominant_decision.value,
                    "sample_count": p.sample_count,
                    "confidence": p.confidence
                }
                for domain, p in profile.domain_profiles.items()
            ],
            "created_at": profile.created_at.isoformat(),
            "last_updated": profile.last_updated.isoformat()
        }

    def explain_profile(
        self,
        domain_tag: DomainTag,
        organization_id: str = "default"
    ) -> str:
        """
        프로필을 사람이 읽을 수 있는 문장으로 설명.

        "이 조직은 언제 멈추는가"를 명확히 표현.

        Args:
            domain_tag: 도메인
            organization_id: 조직 ID

        Returns:
            설명 문장
        """
        domain_profile = self.get_domain_profile(domain_tag, organization_id)

        if not domain_profile:
            return f"No organizational profile found for domain '{domain_tag.value}'."

        # 성격 설명
        strength_desc = {
            "VERY_CONSERVATIVE": "매우 보수적이며 대부분의 경우 실행을 중단하거나 보류합니다",
            "CONSERVATIVE": "보수적이며 확실한 증거 없이는 진행하지 않습니다",
            "BALANCED": "균형적이며 상황에 따라 유연하게 판단합니다",
            "PERMISSIVE": "허용적이며 대부분의 요청을 진행합니다",
            "VERY_PERMISSIVE": "매우 허용적이며 거의 모든 요청을 허용합니다"
        }

        desc = f"이 조직은 '{domain_tag.value}' 도메인에서 "
        desc += strength_desc.get(
            domain_profile.boundary_strength.value,
            "판단 성향을 보입니다"
        )
        desc += f".\n\n"

        # 판단 통계
        desc += f"판단 분포:\n"
        desc += f"  - STOP: {domain_profile.stop_bias:.1%}\n"
        desc += f"  - HOLD: {domain_profile.hold_bias:.1%}\n"
        desc += f"  - ALLOW: {domain_profile.allow_bias:.1%}\n\n"

        # 빈번한 이유
        if domain_profile.frequent_reasons:
            desc += f"주요 판단 이유:\n"
            for reason in domain_profile.frequent_reasons:
                desc += f"  - {reason.value}\n"
            desc += "\n"

        # 고위험 패턴
        if domain_profile.high_risk_patterns:
            desc += f"감지된 고위험 패턴:\n"
            for pattern in domain_profile.high_risk_patterns:
                desc += f"  - {pattern}\n"
            desc += "\n"

        # 신뢰도 및 샘플
        desc += f"프로필 신뢰도: {domain_profile.confidence} "
        desc += f"({domain_profile.sample_count}개 판단 기반)\n"
        desc += f"시간 안정성: {domain_profile.temporal_stability:.1%}"

        return desc
