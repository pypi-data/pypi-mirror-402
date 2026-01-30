import requests

from splight_runner.api.settings import settings


class StatusReporter:
    """Class responsible for updating the component status each time the
    healthcheck method is called.
    """

    _SPL_PREFIX = "Splight"
    _BASE_PATH = "engine/component/components"

    def __init__(
        self,
        api_host: str,
        access_id: str,
        secret_key: str,
        component_id: str,
        api_version: str,
    ):
        self._api_host = api_host.rstrip("/")
        self._component_id = component_id
        self._auth_header = {
            "Authorization": f"{self._SPL_PREFIX} {access_id} {secret_key}"
        }
        self._api_version = api_version
        self._prev_status: str = "Unknown"

    def report_status(self, status: str) -> None:
        """Updates the status of the component in the Splight Platform making
        POST request to the API.

        Parameters
        ----------
        status : str
            The status of the component.
            It can be "Running", "Stopped" or "Succeeded".
        """
        if self._prev_status == status:
            return None
        url = f"{self._api_host}/{self._api_version}/{self._BASE_PATH}"
        url = f"{url}/{self._component_id}/update-status/"
        response = requests.post(
            url, headers=self._auth_header, data={"deployment_status": status}
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            print("Unable to update component status")
            print(exc)
        self._prev_status = status
        return None


reporter = StatusReporter(
    api_host=settings.splight_platform_api_host,
    access_id=settings.access_id,
    secret_key=settings.secret_key,
    component_id=settings.process_id,
    api_version=settings.api_version,
)
