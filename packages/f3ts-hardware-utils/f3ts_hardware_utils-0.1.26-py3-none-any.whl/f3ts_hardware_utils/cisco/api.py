"""Fixture Controller FastAPI Router."""

import os
import threading

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder

from .serial_interface import CatalystSerial

router = APIRouter()


class TimeoutLock:
    """Threading lock wrapper to add timeout to API Calls.

    :raises TimeoutError: Raise if lock isn't acquired within timeout
    """

    timeout = None
    lock = None

    def __init__(self, timeout: float = None, *args, **kwargs):
        """Initialize threading lock with timeout settings."""
        self.timeout = timeout
        self.lock = threading.Lock(*args, **kwargs)

    def __enter__(self, *args, **kwargs):
        """Enter threading lock with timeout."""
        rc = self.lock.acquire(timeout=self.timeout)
        if rc is False:
            raise TimeoutError(f"Could not acquire lock within {self.timeout}s")
        return rc

    def __exit__(self, *args, **kwargs):
        """Exit threading lock."""
        return self.lock.release()

    def acquire(self, *args, **kwargs):
        """Acquire threading lock."""
        return self.lock.acquire(*args, **kwargs)

    def release(self, *args, **kwargs):
        """Release threading lock."""
        return self.lock.release(*args, **kwargs)

    def locked(self, *args, **kwargs):
        """Check threading lock."""
        return self.lock.locked(*args, **kwargs)


# Usage:
lock = TimeoutLock(timeout=60)
router.USERNAME = os.getenv("CISCO_USERNAME", "FixturFab")
router.PASSWORD = os.getenv("CISCO_PASSWORD", "password")
router.PORT = None
router.TIMEOUT = 8


def get_cisco():
    """Get Cisco Catalyst 1200 serial console interface."""
    cisco = None
    try:
        cisco = CatalystSerial(
            username=router.USERNAME,
            password=router.PASSWORD,
            port=router.PORT,
            timeout=router.TIMEOUT,
        )
        router.PORT = cisco.port
    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Unable to connect to serial device" + jsonable_encoder(cisco),
        )

    try:
        yield cisco
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected Error: {e}",
        )
    finally:
        if cisco:
            cisco.console.close()


@router.get("/serial/config", status_code=200)
def get_serial_config(
    cisco: CatalystSerial = Depends(get_cisco),
):
    """Get cisco console serial interface configuration."""
    return cisco


@router.post("/serial/config", status_code=200)
def set_serial_config(
    username: str = "", password: str = "", port: str = None, timeout: float = 1
):
    """
    Set fixture controller serial interface configuration.

    Set port to None for autodiscovery.
    """
    router.USERNAME = username
    router.PASSWORD = password
    router.PORT = port
    router.TIMEOUT = timeout

    try:
        cisco = CatalystSerial(
            username=router.USERNAME,
            password=router.PASSWORD,
            port=router.PORT,
            timeout=router.TIMEOUT,
        )
        cisco.console.close()
        return cisco
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to connect to serial device \
            {jsonable_encoder(cisco)}",
        )


@router.get("/login", status_code=200)
def check_login(
    cisco: CatalystSerial = Depends(get_cisco),
) -> bool:
    """Check if logged into serial interface.

    :param cisco: Cisco serial interface, defaults to Depends(get_cisco)
    :type cisco: CatalystSerial, optional
    :return: True if logged into the Cisco Switch
    :rtype: bool
    """
    with lock:
        output = cisco.check_logged_in()
        return output


@router.post("/login", status_code=200)
def login(
    cisco: CatalystSerial = Depends(get_cisco),
) -> str:
    """Log into serial interface.

    :param cisco: Cisco serial interface, defaults to Depends(get_cisco)
    :type cisco: CatalystSerial, optional
    :return: Login state
    :rtype: str
    """
    with lock:
        output = cisco.login()
        return output


@router.post("/cmd", status_code=200)
def send_command(
    cmd: str,
    cisco: CatalystSerial = Depends(get_cisco),
) -> str:
    """Send command to Cisco Switch.

    :param cmd: serial command to send to cisco interface
    :type cmd: str
    :param cisco: Cisco serial interface, defaults to Depends(get_cisco)
    :type cisco: CatalystSerial, optional
    :return: stdout from command response
    :rtype: str
    """
    with lock:
        if not cisco.check_logged_in():
            cisco.login()

        output = cisco.send_command(cmd)
        return output


@router.post("/cmds", status_code=200)
def send_commands(
    cmds: str,
    cisco: CatalystSerial = Depends(get_cisco),
) -> list:
    """Send command to Cisco Switch.

    :param cmd: serial command to send to cisco interface
    :type cmd: str
    :param cisco: Cisco serial interface, defaults to Depends(get_cisco)
    :type cisco: CatalystSerial, optional
    :return: stdout from command responses
    :rtype: list
    """
    with lock:
        if not cisco.check_logged_in():
            cisco.login()

        output = cisco.send_commands(cmds)
        return output
