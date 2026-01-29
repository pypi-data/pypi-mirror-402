"""F3TS Plugin Utilities."""
import logging
import os

import requests
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class FixturCNTLAPIClient:
    """F3TS Pytest F3TS Webservice API.

    Object for creating and sending requests to the Test runner backend
    """

    def __init__(
        self,
        api_url: str = os.getenv("PYTEST_API_URL", "pytest-f3ts-api:8886"),
        api_str: str = os.getenv("FFC_API_STR", "/api/v1/hardware/ffc"),
    ):
        """Initialize the F3TS Backend API.

        Store the API URL and number of request retries. A request will be
        retried for the provided number of retries. If it continues to fail,
        an exception will be raised.
        """
        self.api_prefix = f"{api_url}{api_str}"
        self.retries = 3
        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }

    def get_fixture_close(self):
        """Get operator id from run information stored in database"""
        attempt = 0
        status_code = 500
        error_msg = ""
        while attempt < self.retries:
            response = requests.get(
                f"{self.api_prefix}/get_close_state",
                headers=self.headers,
                verify=False,
            )

            if response.status_code == 200:
                return bool(response.json())
            else:
                status_code = response.status_code
                error_msg = response.json()

            attempt += 1

        raise HTTPException(
            status_code,
            f"Unable to access fixture controller, {error_msg}",
        )

    def usb_port_enable(self, state: bool = True, port: int = 1):
        """Enable USB Power and Data.

        :param state: True for port enable, defaults to True
        :type state: bool, optional
        :param port: port number (1-6), defaults to 1
        :type port: int, optional
        :return: serial command output
        :rtype: str
        """
        attempt = 0
        status_code = 500
        error_msg = ""
        while attempt < self.retries:
            response = requests.post(
                f"{self.api_prefix}/usb",
                params={"enable": state, "port": port},
                headers=self.headers,
                verify=False,
            )

            if response.status_code == 200:
                return bool(response.json())
            else:
                status_code = response.status_code
                error_msg = response.json()

            attempt += 1

        raise HTTPException(
            status_code,
            f"Unable to access fixture controller, {error_msg}",
        )

    def usb_port_enable_all(self, state: bool = True):
        """Enable All USB Power and Data.

        :param state: True for port enable, defaults to True
        :type state: bool, optional
        :return: serial command output
        :rtype: str
        """
        attempt = 0
        status_code = 500
        error_msg = ""
        while attempt < self.retries:
            response = requests.post(
                f"{self.api_prefix}/usb/all",
                params={"enable": state},
                headers=self.headers,
                verify=False,
            )

            if response.status_code == 200:
                return bool(response.json())
            else:
                status_code = response.status_code
                error_msg = response.json()

            attempt += 1

        raise HTTPException(
            status_code,
            f"Unable to access fixture controller, {error_msg}",
        )
