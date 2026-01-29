from typing import Dict, List

import requests

from splight_runner.logging import log


class LogClient:
    _WRITE_PATH = "logs/write"

    def __init__(self, host: str, access_id: str, secret_key: str, api_version: str):
        self._host = host.rstrip("/")
        self._auth_header = {
            "Authorization": f"Splight {access_id} {secret_key}"
        }
        self._api_version = api_version

    def send_logs(self, records: List[Dict]) -> None:
        """Sends the logs records to the Serverless Logs API.

        Parameters
        ----------
        records: List[Dict]
            The list of records to send.
        """
        log("Sending log records to Logs API")
        url = f"{self._host}/{self._api_version}/{self._WRITE_PATH}"
        body = {"records": records}
        response = requests.post(url=url, json=body, headers=self._auth_header)
        response.raise_for_status()
        return None
