from typing import List

import requests

from drax_sdk.model.dto import DataRequest, DataResponse


class DataMinerClient:
    service_url = ""
    api_key = ""
    api_secret = ""

    def __init__(self, service_url: str, api_key: str, api_secret: str):
        self.service_url = service_url
        self.api_key = api_key
        self.api_secret = api_secret

    def _get_headers(self):
        return {"drax-api-key": self.api_key, "drax-api-secret": self.api_secret}

    def get_supported_aggregation_functions(self) -> List[str]:
        """Get supported aggregation functions"""
        response = requests.get(
            self.service_url + "/aggregation-functions",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    def get_supported_aggregation_periods(self) -> List[str]:
        """Get supported aggregation periods"""
        response = requests.get(
            self.service_url + "/aggregation-periods",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    def get_supported_time_windows(self) -> List[str]:
        """Get supported time windows"""
        response = requests.get(
            self.service_url + "/time-windows",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

    def fetch(self, data_request: DataRequest) -> DataResponse:
        """Fetch data based on request"""
        response = requests.post(
            self.service_url + "/data",
            json=data_request.model_dump(by_alias=True),
            headers={
                **self._get_headers(),
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        response.raise_for_status()
        return DataResponse.model_validate(response.json())
