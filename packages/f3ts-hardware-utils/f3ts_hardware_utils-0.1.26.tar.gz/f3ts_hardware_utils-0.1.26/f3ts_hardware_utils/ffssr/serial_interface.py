# !/usr/bin/env python
"""FixturFab FixturSSR Controller Board Interface."""

import logging
import statistics
from typing import List, Optional

import serial
from serial.tools import list_ports

__author__ = "D. Wilkins"
__version__ = "0.1.0"
__email__ = "dave@fixturfab.com"

# """" Uncomment for logger output to console
logger = logging.getLogger(__name__)
logger.setLevel(
    logging.WARNING
)  # Adjust level as needed (DEBUG, INFO, WARNING, ERROR, etc.)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
# """


class FixturSSRException(Exception):
    """Custom exception class for FixturSSR errors."""

    pass


class FixturSSR:
    """FixturFab Solid-state Relay Mux Controller Serial Interface."""

    def __init__(
        self,
        port: str = "",
        baud: int = 57600,
        timeout: int = 1,
        card_id: Optional[int] = None,
    ):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None
        self.card_id = card_id

    def __del__(self):
        self.close()

    # ##################################################################################
    # Serial Discovery & Connection
    # ##################################################################################

    def open(self) -> None:
        """Open serial port on FixturFab FixturSSR Controller.

        Raises:
            FixturSSRException:
                If no matching device is found or if there's an error in connection.
        """
        try:
            if self.port:
                self._connect_to_port(self.port)
            else:
                self._auto_discover_and_connect()
        except IOError as e:
            raise FixturSSRException(f"Failed to open FixturSSR port: {e}")

    def close(self) -> None:
        """Close the FixturSSR Controller serial interface."""
        if self.serial and self.serial.is_open:
            logger.debug("Closing serial interface")
            self.serial.close()
            self.serial = None

    def list_ports(self) -> List[str]:
        """ "Return a list of FixturSSR serial ports ennumerated in system."""
        ports_list = list_ports.comports()
        rp2040_ports = [port for port, desc, hwid in ports_list if "2E8A:000A" in hwid]
        logger.debug(f"Found these possible serial ports in system {rp2040_ports}")

        fixturssr_ports = []
        for port in rp2040_ports:
            if self._is_fixturssr_board(port):
                fixturssr_ports.append(port)
        return fixturssr_ports

    def _connect_to_port(self, port: str) -> None:
        """Helper method to connect to a specific port."""
        if self._is_fixturssr_board(port):
            logger.debug(f"Opening FixturSSR Controller interface port={port}")
            self.serial = serial.Serial(port, self.baud, timeout=self.timeout)
            if self.card_id is not None:
                logger.debug(f"Checking card_id={self.card_id} @ port={port}")
                if self.card_identifier() != self.card_id:
                    raise FixturSSRException(
                        f"Found FixturSSR device at port={self.port} "
                        + f"but doesn't match specified card_id={self.card_id}"
                    )
            self.port = port
        else:
            raise FixturSSRException(f"Resource at port={port} is not a FixturSSR card")

    def _auto_discover_and_connect(self) -> None:
        """Helper method to automatically discover and connect to a FixturSSR device."""
        fixturssr_ports = self.list_ports()
        card_id_match = []

        if not fixturssr_ports:
            raise FixturSSRException("No FixturSSR devices found in system")
        if len(fixturssr_ports) > 1 and self.card_id is None:
            raise FixturSSRException(
                f"{len(fixturssr_ports)} FixturSSR devices found in system, "
                + "use port or card_id to differentiate devices"
            )

        for port in fixturssr_ports:
            if self.card_id is None:
                card_id_match.append(port)
            else:
                logger.debug(
                    f"Opening target serial interface port={port} (to check card_id)"
                )
                self.serial = serial.Serial(port, self.baud, timeout=self.timeout)
                if self.card_identifier() == self.card_id:
                    logger.debug(
                        f"-> Found matching card_id={self.card_id} @ port={port}"
                    )
                    card_id_match.append(port)
            self.close()

        if len(card_id_match) == 0:  # No card_id matches, bummer
            raise FixturSSRException(
                f"No FixturSSR devices found in system with card_id = {self.card_id}"
            )

        if len(card_id_match) > 1:  # Too many card_id matches, can't differentiate
            raise FixturSSRException(
                f"More than one FixurIO device with card_id = {self.card_id}, "
                + "cannot differentiate"
            )

        self.port = card_id_match[0]  # Must be a list of one port
        logger.debug(
            f"Opening target serial interface port={self.port} (final binding)"
        )
        self.serial = serial.Serial(self.port, self.baud, timeout=self.timeout)

    def _is_fixturssr_board(self, port: str) -> bool:
        """Check if the device at the given port is a FixturSSR board."""
        logger.debug(f"Checking if device at port={port} is a FixturSSR board")
        try:
            logger.debug(
                f"Opening target serial interface port={port} (to check mfg and mpn)"
            )
            self.serial = serial.Serial(port, self.baud, timeout=self.timeout)
            is_fixturssr = (
                "FixturFab" in self.manufacturer() and "101-0425-" in self.part_number()
            )
            if is_fixturssr:
                logger.debug(f"Device @ {self.serial.name} is a FixturSSR device")
            else:
                logger.debug(f"Device @ {self.serial.name} is not a FixturSSR device")
            self.close()
            return is_fixturssr
        except serial.SerialException as e:
            raise FixturSSRException(f"Serial communication error: {e}")
        except FixturSSRException:
            logger.debug(f"Device @ {self.serial.name} is not a FixturSSR device")
            self.close()
            return False

    def who(self) -> str:
        """Get the manufacturer string."""
        return self.get_command("who")

    def part_number(self) -> str:
        """Get the part number string."""
        return self.get_command("mpn")

    def card_identifier(self) -> int:
        """Get the card identifier number."""
        return int(self.get_command("card"))

    def manufacturer(self) -> str:
        """Get the manufacturer identification string."""
        return self.get_command("mfg")

    def fw_version(self) -> int:
        """Get the firmware version number."""
        return int(self.get_command("fw"))

    def reset(self) -> None:
        self.set_command("reset")
        self.close()

    # ##################################################################################
    # Console Commands / Returns
    # ##################################################################################

    def set_command(self, command_str: str) -> None:
        """Send a serial command to the FixturSSR Controller and check for
        acknowledgment, no response expected."""
        if not self.serial:
            raise FixturSSRException(
                "set_command: Not connected to FixturSSR Controller serial interface"
            )
        self._send_command(command_str)
        status = self._read_line()
        if "OK" not in status:
            raise FixturSSRException(f"Command '{command_str}' failed: {status}")

    def get_command(self, command_str: str) -> str:
        """Send a serial command to query the FixturSSR Controller, check for
        acknowledgement, return the response."""
        if not self.serial:
            raise FixturSSRException(
                "get_command: Not connected to FixturSSR Controller serial interface"
            )
        self._send_command(command_str)
        output = self._read_line()
        if "KO -" in output:
            raise FixturSSRException(f"Command '{command_str}' failed: {output}")
        status = self._read_line()
        if "OK" not in status:
            raise FixturSSRException(f"Command '{command_str}' failed: {output}")
        return output.strip()

    def _send_command(self, command_str: str) -> None:
        """Send a command string to the serial port."""
        logger.debug(f"Sending command: {command_str}")
        self.serial.write(bytes(f"{command_str}\r", "utf-8"))

    def _read_line(self) -> str:
        """Read a line from the serial port."""
        line = self.serial.readline().decode("utf-8").strip()
        logger.debug(f"Received: {line}")
        return line

    # ##################################################################################
    # Relay Mux Commands
    # ##################################################################################

    def mux_chan_enable(self, channel: int) -> None:
        """Enable a particular Mux channel (all other channels are automatically
        disabled).  Only one Mux channel can be enabled coincidently.

        Args:
            channel: 1-16 (int)

        Returns:
            None
        """
        assert channel >= 1 and channel <= 16, "Mux channel must be 1-16"
        self.set_command(f"muxon {channel}")

    def mux_off(self) -> None:
        """Disables any currently enabled Mux channel

        Args:
            None

        Returns:
            None
        """
        self.set_command("muxoff")

    def mux_adc(self, terminal: str = "+", average: int = 1) -> int:
        """Perform ADC reading on the + or - terminal of whatever Mux channel
        is currently enabled.  Reading is referenced to ground, and has 12-bit
        resolution (0-4095).  Note that jumpers on board must be in "ADC" position.

        Args:
            terminal: physical terminal to take reading ("+" or "-")
            average: average over this number of successive readings (int)

        Returns:
            Decimal ADC reading (int)
        """
        assert (
            terminal == "+" or terminal == "-"
        ), "Must select + or - terminal block for ADC reading"
        assert average >= 1, "Argument for reading average must be >=1"
        adc = []
        for i in range(average):
            if terminal == "+":
                adc.append(int(self.get_command("adc+")))
            else:
                adc.append(int(self.get_command("adc-")))
        return int(round(statistics.mean(adc)))

    def mux_voltage(self, terminal: str = "+", average: int = 1) -> float:
        """Perform ADC reading on the + or - terminal of whatever Mux channel is
        currentlyenabled, and calculate voltage.  Reading is referenced to ground.
        Note that jumpers on board must be in "ADC" position.

        Args:
            terminal: physical terminal to take reading ("+" or "-")
            average: average over this number of successive readings (int)

        Returns:
            One or more ASCII characters representing the Voltage reading (float)
        """
        assert (
            terminal == "+" or terminal == "-"
        ), "Must select + or - terminal block for Voltage reading"
        assert average >= 1, "Argument for reading average must be >=1"
        adc = []
        for i in range(average):
            if terminal == "+":
                adc.append(int(self.get_command("adc+")))
            else:
                adc.append(int(self.get_command("adc-")))

        voltage = statistics.mean(adc) * 3.3 / 4095  # 12-bit ADC to Volts
        return voltage
