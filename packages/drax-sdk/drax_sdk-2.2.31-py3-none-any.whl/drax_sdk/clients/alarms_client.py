from typing import List

import requests

from drax_sdk.model.dto import (
    Alarm,
    AlarmType,
    AlarmLogEntry,
    AcknowledgeAlarmRequest,
    ResolveAlarmRequest,
    FindAlarmLogEntriesRequest,
    FindAlarmTypesRequest,
    FindAlarmsRequest,
    PagedResult,
)


class AlarmsClient:
    service_url = ""
    api_key = ""
    api_secret = ""

    def __init__(self, service_url: str, api_key: str, api_secret: str):
        self.service_url = service_url
        self.api_key = api_key
        self.api_secret = api_secret

    def _get_headers(self):
        return {"drax-api-key": self.api_key, "drax-api-secret": self.api_secret}

    def get_alarm_collection_strategy_types(self) -> List[str]:
        """Get alarm collection strategy types"""
        response = requests.get(
            self.service_url + "/alarm-collection-strategy-types",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    def get_alarm_scope_types(self) -> List[str]:
        """Get alarm scope types"""
        response = requests.get(
            self.service_url + "/alarm-scope-types",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    def get_alarm_severity_types(self) -> List[str]:
        """Get alarm severity types"""
        response = requests.get(
            self.service_url + "/alarm-severity-types",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    def get_alarm_status_types(self) -> List[str]:
        """Get alarm status types"""
        response = requests.get(
            self.service_url + "/alarm-status-types",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    def get_alarm_type_statuses(self) -> List[str]:
        """Get alarm type statuses"""
        response = requests.get(
            self.service_url + "/alarm-type-statuses",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    def acknowledge(self, acknowledge_request: AcknowledgeAlarmRequest) -> Alarm:
        """Acknowledge an alarm"""
        response = requests.post(
            self.service_url + "/alarm/acknowledge",
            json=acknowledge_request.model_dump(by_alias=True),
            headers={**self._get_headers(), "Content-Type": "application/json"},
        )
        response.raise_for_status()
        return Alarm.model_validate(response.json())

    def delete(self, project_id: str, alarm_id: str) -> None:
        """Delete an alarm"""
        response = requests.delete(
            self.service_url + f"/{project_id}/alarms/{alarm_id}",
            headers=self._get_headers(),
        )
        response.raise_for_status()

    def delete_alarm_type(self, alarm_type_id: str) -> None:
        """Delete an alarm type"""
        response = requests.delete(
            self.service_url + f"/alarm-types/{alarm_type_id}",
            headers=self._get_headers(),
        )
        response.raise_for_status()

    def find_alarm_log_entries(
        self, find_request: FindAlarmLogEntriesRequest
    ) -> PagedResult[AlarmLogEntry]:
        """Find alarm log entries"""
        response = requests.post(
            self.service_url + "/alarm-log-entries",
            json=find_request.model_dump(by_alias=True),
            headers={**self._get_headers(), "Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        # Extract from response envelope
        if "value" in data:
            data = data["value"]
        return PagedResult[AlarmLogEntry].model_validate(data)

    def find_alarm_types(self, find_request: FindAlarmTypesRequest) -> PagedResult[AlarmType]:
        """Find alarm types"""
        response = requests.post(
            self.service_url + "/alarm-types",
            json=find_request.model_dump(by_alias=True),
            headers={**self._get_headers(), "Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        # Extract from response envelope
        if "value" in data:
            data = data["value"]
        return PagedResult[AlarmType].model_validate(data)

    def find_alarms(self, find_request: FindAlarmsRequest) -> PagedResult[Alarm]:
        """Find alarms"""
        response = requests.post(
            self.service_url + "/alarms",
            json=find_request.model_dump(by_alias=True),
            headers={**self._get_headers(), "Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        # Extract from response envelope
        if "value" in data:
            data = data["value"]
        return PagedResult[Alarm].model_validate(data)

    def get_alarm(self, alarm_id: str) -> Alarm:
        """Get an alarm by id"""
        response = requests.get(
            self.service_url + f"/alarm/{alarm_id}",
            headers={**self._get_headers(), "Accept": "application/json"},
        )
        response.raise_for_status()
        return Alarm.model_validate(response.json())

    def get_alarm_type(self, alarm_type_id: str) -> AlarmType:
        """Get an alarm type by id"""
        response = requests.get(
            self.service_url + f"/alarm-types/{alarm_type_id}",
            headers={**self._get_headers(), "Accept": "application/json"},
        )
        response.raise_for_status()
        return AlarmType.model_validate(response.json())

    def resolve(self, resolve_request: ResolveAlarmRequest) -> Alarm:
        """Resolve an alarm"""
        response = requests.post(
            self.service_url + "/alarm/resolve",
            json=resolve_request.model_dump(by_alias=True),
            headers={**self._get_headers(), "Content-Type": "application/json"},
        )
        response.raise_for_status()
        return Alarm.model_validate(response.json())

    def save_alarm_type(self, alarm_type: AlarmType) -> AlarmType:
        """Save an alarm type"""
        response = requests.put(
            self.service_url + "/alarm-types",
            json=alarm_type.model_dump(by_alias=True),
            headers={**self._get_headers(), "Content-Type": "application/json"},
        )
        response.raise_for_status()
        return AlarmType.model_validate(response.json())
