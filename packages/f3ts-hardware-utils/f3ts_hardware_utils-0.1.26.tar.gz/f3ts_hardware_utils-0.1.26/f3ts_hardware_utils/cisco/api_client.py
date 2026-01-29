"""F3TS Plugin Utilities."""

import logging
import os
import subprocess

import requests
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class CiscoAPIClient:
    """Cisco Switch hardware API String.

    Object for creating and sending requests to the Test runner backend
    """

    def __init__(
        self,
        api_url: str = os.getenv("PYTEST_API_URL", "pytest-f3ts-api:8886"),
        api_str: str = os.getenv("CISCO_API_STR", "/api/v1/hardware/cisco"),
        api_timeout: float = 60,
    ):
        """Initialize the F3TS Backend API.

        Store the API URL and number of request retries. A request will be
        retried for the provided number of retries. If it continues to fail,
        an exception will be raised.
        """
        self.api_timeout = api_timeout
        self.api_prefix = f"{api_url}{api_str}"
        self.retries = 3
        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }

        self.session = requests.Session()

    def login(self):
        """Login to Cisco Switch.

        :raises HTTPException: Raise error when unable to connect to Cisco API
        :return: Login state
        :rtype: bool
        """
        attempt = 0
        status_code = 500
        error_msg = ""
        while attempt < self.retries:
            response = self.session.post(
                f"{self.api_prefix}/login",
                headers=self.headers,
                verify=False,
                timeout=self.api_timeout,
            )

            if response.status_code == 200:
                return bool(response.json())
            else:
                status_code = response.status_code
                try:
                    error_msg = response.json()
                except Exception:
                    error_msg = response.text

            attempt += 1

        raise HTTPException(
            status_code,
            f"Unable to access cisco client, {error_msg}",
        )

    def check_login(self):
        """Check login to Cisco Switch.

        :raises HTTPException: Raise error when unable to connect to Cisco API
        :return: Login state
        :rtype: bool
        """
        attempt = 0
        status_code = 500
        error_msg = ""
        while attempt < self.retries:
            response = self.session.get(
                f"{self.api_prefix}/login",
                headers=self.headers,
                verify=False,
                timeout=self.api_timeout,
            )

            if response.status_code == 200:
                return bool(response.json())
            else:
                status_code = response.status_code
                try:
                    error_msg = response.json()
                except Exception:
                    error_msg = response.text

            attempt += 1

        raise HTTPException(
            status_code,
            f"Unable to access cisco client, {error_msg}",
        )

    def enable_poe(self, port, state):
        """Set PoE enable state to a particular ethernet port.

        :param port: Cisco port
        :type port: int
        :param state: True if POE Enabled
        :type state: bool
        :raises HTTPException: Raise error when unable to connect to Cisco API
        :return: Request completed
        :rtype: bool
        """
        mode = "never"
        if state:
            mode = "auto"

        commands = (
            f"configure,interface GigabitEthernet {port},power inline {mode},exit,exit"
        )

        attempt = 0
        status_code = 500
        error_msg = ""
        while attempt < self.retries:
            response = self.session.post(
                f"{self.api_prefix}/cmds",
                params={"cmds": commands},
                headers=self.headers,
                verify=False,
                timeout=self.api_timeout,
            )

            if response.status_code == 200:
                return bool(response.json())
            else:
                status_code = response.status_code
                try:
                    error_msg = response.json()
                except Exception:
                    error_msg = response.text

            attempt += 1

        raise HTTPException(
            status_code,
            f"Unable to access cisco client, {error_msg}",
        )

    def get_ip(self, port):
        """Get IP Address from a particular ethernet port.

        :param port: Cisco port
        :type port: int
        :raises HTTPException: Raise error when unable to connect to Cisco API
        :return: Request completed
        :rtype: bool
        """
        command = f"show mac address-table interface GigabitEthernet {port}"

        attempt = 0
        status_code = 500
        error_msg = ""
        while attempt < self.retries:
            response = self.session.post(
                f"{self.api_prefix}/cmd",
                params={"cmd": command},
                headers=self.headers,
                verify=False,
                timeout=self.api_timeout,
            )

            if response.status_code == 200:
                out = response.json()
                mac_addr = out.split("\r\r\n")[5].split()[1]

                out = subprocess.check_output(["nmap", "-snP", "192.168.30.0/24"])
                out = out.decode("utf-8").split("Nmap scan report for ")
                for device in out:
                    if mac_addr.upper() in device:
                        return device.split("\n")[0]

            else:
                status_code = response.status_code
                try:
                    error_msg = response.json()
                except Exception:
                    error_msg = response.text

            attempt += 1

        raise HTTPException(
            status_code,
            f"Unable to access cisco client, {error_msg}",
        )
