"""Pylink JLink Interface."""
import os.path

import pylink


class JLink:
    """Custom JLink Wrapper using pylink."""

    def __init__(self, jlink_serial: str, mcu_name: str):
        """Initialize pylink JLink Interface."""
        self.jlink = pylink.JLink()
        self.JLINK_SERIAL = jlink_serial
        self.MCU_NAME = mcu_name

    def reset(self):
        """Reset target."""
        self.jlink.reset()

    def open_and_connect(self):
        """Use pylink and JLink interface to connect to MCU."""
        # Connect to JLink
        try:
            if not self.jlink.opened():
                self.jlink.open(self.JLINK_SERIAL)  # Connect to JLink Module
            self.jlink.set_tif(
                pylink.JLinkInterfaces.SWD
            )  # Set SWD as communication protocol
        except Exception as e:
            raise OSError(f"Error connecting to JLink: {e}") from e

        # Check if JLink is connected
        if not self.jlink.opened():
            raise AssertionError("No JLink is connected")

        # Connect to MCU
        try:
            self.jlink.connect(self.MCU_NAME, "auto")  # Connect to MCU from JLink
            self.jlink.reset()  # Reset for settings to take effect
        except Exception as e:
            raise OSError(f"Error with connecting to MCU over JLink: {e}") from e

        # Check if MCU is connected
        if not self.jlink.target_connected():
            raise AssertionError("No MCU is connected to JLink")

    def erase_fw(self):
        """Use pylink and JLink interface to erase rvc_firmware from MCU."""
        # Erase existing rvc_firmware from device
        try:
            self.jlink.erase()
        except Exception as e:
            raise Exception(f"Error erasing firmware from MCU: {e}") from e

    def flash_file(self, firmware, address):
        """Flash firmware file to specified byte address.

        :param firmware: absolute path to firmware file
        :type firmware: str
        :param address: start of address to start flash
        :type address: int
        """
        # Verify file exists:
        if not os.path.isfile(firmware):
            raise AssertionError(f"Firmware file on path {firmware} cannot be found")

        # Flash firmware file at given address:
        try:
            self.jlink.flash_file(firmware, address)
        except Exception as e:
            raise Exception(f"Error flashing firmware to MCU: {e}") from e

    def close(self):
        """Close Jlink hardware interface."""
        self.jlink.close()
