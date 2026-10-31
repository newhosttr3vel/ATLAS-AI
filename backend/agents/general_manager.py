"""General Manager routes requests to the appropriate department crew."""

from typing import Any

from backend.crews.departments import DepartmentsCrew
from backend.crews.sales import SalesCrew
from backend.models import Lead


class GeneralManagerAgent:
    agent_id = "general_manager"

    def __init__(self) -> None:
        self.sales_crew = SalesCrew()
        self.departments_crew = DepartmentsCrew()

    def dispatch(self, task_type: str, lead: Lead, instructions: str | None = None) -> tuple[str, dict[str, Any]]:
        """Route a supported request and return a standardized reviewable response."""
        if task_type in {"qualify_lead", "build_offer"}:
            return self.sales_crew.execute(task_type, lead, instructions)
        return self.departments_crew.execute(task_type, lead, instructions)
