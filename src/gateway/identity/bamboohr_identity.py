import re
from .identity_base import IdentityBase
from ...services.bamboo_hr_service.bamboo_hr import BambooHR

class BambooHRIdentity(IdentityBase):
    def __init__(self, config: dict):
        super().__init__(config)
        self.bamboo_hr_service = BambooHR(config)

    def get_user_info(self, identity: str) -> dict:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", identity):
            raise ValueError("Invalid email address")

        employee_summary = self.bamboo_hr_service.get_employee_summary(identity)
        if employee_summary:
            return employee_summary

        return {"identity": identity}