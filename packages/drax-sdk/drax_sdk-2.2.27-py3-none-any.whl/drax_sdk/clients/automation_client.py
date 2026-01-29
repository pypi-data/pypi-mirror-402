from typing import List

import requests

from drax_sdk.model.automations import Automation
from drax_sdk.model.dto import (
    FindAutomationsRequest,
    FindUserActionsRequest,
    FindUserConditionsRequest,
    FindLogRequest,
    AutomationRequest,
    ExecuteAutomationRequest,
    UserAction,
    UserCondition,
    LogEntry,
    PagedResult,
)


class AutomationClient:
    DEFAULT_PAGE = 1
    DEFAULT_SIZE = 10

    service_url = ""
    api_key = ""
    api_secret = ""

    def __init__(self, service_url: str, api_key: str, api_secret: str):
        self.service_url = service_url
        self.api_key = api_key
        self.api_secret = api_secret

    def _get_headers(self):
        return {"drax-api-key": self.api_key, "drax-api-secret": self.api_secret}

    def automate(
        self, activator_type: str, selector: str, initial_variables: dict = None
    ) -> None:
        """Automate an activator"""
        request = AutomationRequest(
            activator_type=activator_type,
            selector=selector,
            initial_variables=initial_variables or {}
        )
        response = requests.post(
            self.service_url + "/automate",
            json=request.model_dump(by_alias=True),
            headers={**self._get_headers(), "Content-Type": "application/json"},
        )
        response.raise_for_status()

    def delete(self, automation_id: str) -> None:
        """Delete an automation"""
        response = requests.delete(
            self.service_url + f"/automations/{automation_id}",
            headers=self._get_headers(),
        )
        response.raise_for_status()

    def delete_user_action(self, user_action_id: str) -> None:
        """Delete a user action"""
        response = requests.delete(
            self.service_url + f"/user-actions/{user_action_id}",
            headers=self._get_headers(),
        )
        response.raise_for_status()

    def delete_user_condition(self, user_condition_id: str) -> None:
        """Delete a user condition"""
        response = requests.delete(
            self.service_url + f"/user-conditions/{user_condition_id}",
            headers=self._get_headers(),
        )
        response.raise_for_status()

    def find(self, find_request: FindAutomationsRequest) -> PagedResult[Automation]:
        """Find automations based on request"""
        response = requests.post(
            self.service_url + "/automations/find",
            json=find_request.model_dump(by_alias=True),
            headers={**self._get_headers(), "Content-Type": "application/json"},
        )
        response.raise_for_status()
        return PagedResult[Automation].model_validate(response.json())

    def find_user_actions(self, find_request: FindUserActionsRequest) -> PagedResult[UserAction]:
        """Find user actions based on request"""
        response = requests.post(
            self.service_url + "/user-actions/find",
            json=find_request.model_dump(by_alias=True),
            headers={**self._get_headers(), "Content-Type": "application/json"},
        )
        response.raise_for_status()
        return PagedResult[UserAction].model_validate(response.json())

    def find_user_conditions(self, find_request: FindUserConditionsRequest) -> PagedResult[UserCondition]:
        """Find user conditions based on request"""
        response = requests.post(
            self.service_url + "/user-conditions/find",
            json=find_request.model_dump(by_alias=True),
            headers={**self._get_headers(), "Content-Type": "application/json"},
        )
        response.raise_for_status()
        return PagedResult[UserCondition].model_validate(response.json())

    def get_actions(self, project_id: str) -> List[UserAction]:
        """Get actions for a project"""
        response = requests.get(
            self.service_url + f"/actions?projectId={project_id}",
            headers={**self._get_headers(), "Accept": "application/json"},
        )
        response.raise_for_status()
        return [UserAction.model_validate(action) for action in response.json()]

    def get_by_id(self, automation_id: str) -> Automation:
        """Get an automation by id"""
        response = requests.get(
            self.service_url + f"/automations/{automation_id}",
            headers={**self._get_headers(), "Accept": "application/json"},
        )
        response.raise_for_status()
        return Automation.model_validate(response.json())

    def get_conditions(self, project_id: str) -> List[UserCondition]:
        """Get conditions for a project"""
        response = requests.get(
            self.service_url + f"/conditions?projectId={project_id}",
            headers={**self._get_headers(), "Accept": "application/json"},
        )
        response.raise_for_status()
        return [UserCondition.model_validate(cond) for cond in response.json()]

    def get_user_action_by_id(self, user_action_id: str) -> UserAction:
        """Get a user action by id"""
        response = requests.get(
            self.service_url + f"/user-actions/{user_action_id}",
            headers={**self._get_headers(), "Accept": "application/json"},
        )
        response.raise_for_status()
        return UserAction.model_validate(response.json())

    def get_user_condition_by_id(self, user_condition_id: str) -> UserCondition:
        """Get a user condition by id"""
        response = requests.get(
            self.service_url + f"/user-conditions/{user_condition_id}",
            headers={**self._get_headers(), "Accept": "application/json"},
        )
        response.raise_for_status()
        return UserCondition.model_validate(response.json())

    def find_logs(self, log_request: FindLogRequest) -> PagedResult[LogEntry]:
        """Find automation log entries"""
        response = requests.post(
            self.service_url + "/logs/find",
            json=log_request.model_dump(by_alias=True),
            headers={**self._get_headers(), "Content-Type": "application/json"},
        )
        response.raise_for_status()
        return PagedResult[LogEntry].model_validate(response.json())

    def save(self, automation: Automation) -> Automation:
        """Save an automation"""
        response = requests.post(
            self.service_url + "/automations",
            json=automation.model_dump(by_alias=True),
            headers={**self._get_headers(), "Content-Type": "application/json"},
        )
        response.raise_for_status()
        return Automation.model_validate(response.json())

    def save_user_action(self, user_action: UserAction) -> UserAction:
        """Save a user action"""
        response = requests.post(
            self.service_url + "/user-actions",
            json=user_action.model_dump(by_alias=True),
            headers={**self._get_headers(), "Content-Type": "application/json"},
        )
        response.raise_for_status()
        return UserAction.model_validate(response.json())

    def save_user_condition(self, user_condition: UserCondition) -> UserCondition:
        """Save a user condition"""
        response = requests.post(
            self.service_url + "/user-conditions",
            json=user_condition.model_dump(by_alias=True),
            headers={**self._get_headers(), "Content-Type": "application/json"},
        )
        response.raise_for_status()
        return UserCondition.model_validate(response.json())

    def execute_automation(self, execute_request: ExecuteAutomationRequest) -> Automation:
        """Execute an automation"""
        response = requests.post(
            self.service_url + "/automations/execute",
            json=execute_request.model_dump(by_alias=True),
            headers={**self._get_headers(), "Content-Type": "application/json"},
        )
        response.raise_for_status()
        return Automation.model_validate(response.json())
