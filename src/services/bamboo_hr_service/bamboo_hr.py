"""A module to interact with BambooHR API and hold employee data"""

import os
import datetime
import base64
import requests
from ...common.utils import parse_yaml_response
from ...common.prompt_templates import (
    FilterLocationsSystemPrompt,
    FilterLocationsUserPrompt,
)
from ..common.singleton import SingletonMeta


class BambooHR(metaclass=SingletonMeta):
    """A service to interact with BambooHR API and hold employee data"""

    def __init__(self, config: dict = {}) -> None:
        self._api_key = config.get("bamboo_hr_api_key", os.environ.get("BAMBOO_HR_API_KEY"))
        self._base_url = config.get("bamboo_hr_base_url", os.environ.get("BAMBOO_HR_BASE_URL"))
        self._employee_data = None
        self._last_fetch = None

        if not self._api_key:
            raise ValueError("BambooHR API key not set, please set BAMBOO_HR_API_KEY environment variable")
        if not self._base_url:
            raise ValueError("BambooHR base URL not set, please set BAMBOO_HR_BASE_URL environment variable")

    @property
    def employee_data(self) -> dict:
        if not self._employee_data:
            self._employee_data = self.fetch_employee_data()
        elif (datetime.datetime.now() - self._last_fetch).total_seconds() > 12 * 3600:
            # If last fetch was more than 12 hours ago, fetch again
            self._employee_data = self.fetch_employee_data()
        return self._employee_data

    def get_employee(self, email: str) -> dict:
        return self.employee_data.get(email.lower())

    def get_employee_summary(self, email: str) -> dict:
        employee = self.get_employee(email)
        if not employee:
            return None
        return {
            "name": employee.get("displayName"),
            "title": employee.get("jobTitle"),
            "email": employee.get("workEmail"),
            "phone": employee.get("workPhone"),
            "mobile": employee.get("mobilePhone"),
            "department": employee.get("department"),
            "location": employee.get("location"),
            "supervisor": employee.get("supervisor"),
        }

    def get_away_info(self, email: str, days_away: int = 30) -> str:
        now = datetime.datetime.now()
        start = datetime.datetime.strftime(now, "%Y-%m-%d")
        end = datetime.datetime.strftime(now + datetime.timedelta(days=days_away), "%Y-%m-%d")

        url = os.path.join(self._base_url, "time_off/whos_out")
        response = self.api_request(url, {"start": start, "end": end})
        away_info = {}
        for away_employee in response:
            eid = str(away_employee.get("employeeId"))
            if eid not in away_info:
                away_info[eid] = []
            away_info[eid].append(
                {
                    "name": away_employee.get("name"),
                    "start": away_employee.get("start"),
                    "end": away_employee.get("end"),
                }
            )
        employee = self.get_employee(email)
        if not employee:
            return None
        employee_id = employee.get("id")
        employee_away_info = away_info.get(employee_id, [])
        return {
            "employee": employee.get("displayName"),
            "away_info": employee_away_info,
        }

    def get_reports(self, email: str, levels: int = -1) -> list:
        employee = self.get_employee(email)
        if not employee:
            return None
        reports = []
        self.get_reports_recursive(employee, reports, levels)
        return reports

    def get_all_employees(self) -> list:
        return list(self.employee_data.values())

    def get_reports_recursive(self, employee, reports, levels):
        if levels == 0:
            return
        if employee.get("reports"):
            for report in employee.get("reports"):
                reports.append(report)
                self.get_reports_recursive(report, reports, levels - 1)

    def get_list_of_all_locations(self) -> list:
        # Go through all employees and get the location
        locations = set()
        for employee in self.employee_data.values():
            location = employee.get("location")
            if location:
                locations.add(location)
        return sorted(list(locations))

    def get_employees_by_location(self, location: str, llm_service_fn: callable) -> list:
        # We are going to use an LLM to decide if Bamboo locations should
        # be included in the list of locations
        if not llm_service_fn:
            raise ValueError("LLM service function not set in BambooHR instance")
        response = llm_service_fn(
            [
                {
                    "role": "system",
                    "content": FilterLocationsSystemPrompt(self.get_list_of_all_locations()),
                },
                {"role": "user", "content": FilterLocationsUserPrompt(location)},
            ]
        ).get("content")

        response = parse_yaml_response(response)
        employees = []
        if response and isinstance(response, dict) and response.get("matching_locations"):
            location_set = set(response["matching_locations"])
            for employee in self.employee_data.values():
                if employee.get("location") in location_set:
                    employees.append(employee)
        return employees

    def fetch_employee_data(self) -> dict:
        # First fetch the directory report from Bamboo
        url = os.path.join(self._base_url, "employees/directory")
        response = self.api_request(url)
        employee_data = self.build_org_chart(response)

        self._last_fetch = datetime.datetime.now()
        self._employee_data = employee_data
        return employee_data

    def api_request(self, url: str, params: dict = None) -> dict:
        basic_auth = self.encode_basic_auth(self._api_key, "x")
        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Accept": "application/json",
        }
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch data: {response.status_code}")
        return response.json()

    def build_org_chart(self, directory_report) -> dict:
        employee_data = {}
        by_name = {}
        for employee in directory_report.get("employees", []):
            email = employee.get("workEmail")
            if not email:
                continue
            employee_data[email.lower()] = employee
            by_name[employee["displayName"]] = employee

        for employee in directory_report.get("employees", []):
            manager_name = employee.get("supervisor")
            if manager_name:
                manager = by_name.get(manager_name)
                if manager:
                    manager["reports"] = manager.get("reports", [])
                    manager["reports"].append(employee)
                    employee["manager"] = manager
        return employee_data

    def encode_basic_auth(self, username: str, password: str) -> str:
        user_pass = f"{username}:{password}"
        encoded_bytes = base64.b64encode(user_pass.encode("utf-8"))
        encoded_str = str(encoded_bytes, "utf-8")
        return encoded_str
