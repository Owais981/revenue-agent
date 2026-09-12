"""Adapter interfaces for external systems the Revenue Agent will eventually integrate
with. Each has a Mock implementation so the MVP runs standalone with no external
services required. Swap the Mock* class for a real implementation later without
touching calling code."""
from abc import ABC, abstractmethod
from typing import Optional


class CRMAdapter(ABC):
    @abstractmethod
    async def find_account(self, name: str) -> Optional[dict]:
        ...

    @abstractmethod
    async def write_lead(self, lead: dict) -> bool:
        ...


class MockCRMAdapter(CRMAdapter):
    async def find_account(self, name: str) -> Optional[dict]:
        return None

    async def write_lead(self, lead: dict) -> bool:
        return True


class PlanningAdapter(ABC):
    @abstractmethod
    async def check_capacity(self, location: Optional[str], window: Optional[str]) -> dict:
        ...


class MockPlanningAdapter(PlanningAdapter):
    """DEMO / MANUAL CAPACITY DATA. Replace with the real Planning Agent integration.

    Returns a deterministic-but-varied capacity signal so the deliverability score has
    something believable to compute against until real crew/kit calendars are wired in.
    """

    async def check_capacity(self, location: Optional[str], window: Optional[str]) -> dict:
        return {
            "crew_available": True,
            "equipment_available": True,
            "pipeline_load_pct": 55,
            "note": "DEMO / MANUAL CAPACITY DATA - Planning Agent not yet integrated",
        }


class FinanceAdapter(ABC):
    @abstractmethod
    async def get_credit_status(self, account_id: str) -> dict:
        ...


class MockFinanceAdapter(FinanceAdapter):
    async def get_credit_status(self, account_id: str) -> dict:
        return {"overdue": False, "expected_margin_band": "medium"}


class KnowledgeAdapter(ABC):
    @abstractmethod
    async def find_similar_case_study(self, service: Optional[str], industry: Optional[str]) -> Optional[dict]:
        ...


class MockKnowledgeAdapter(KnowledgeAdapter):
    async def find_similar_case_study(self, service: Optional[str], industry: Optional[str]) -> Optional[dict]:
        if not service:
            return None
        return {
            "title": f"{service} project for a comparable {industry or 'industry'} client",
            "summary": "A similar project delivered on time and on budget (demo case study).",
            "internal_record_id": "CASE-DEMO-001",
        }
