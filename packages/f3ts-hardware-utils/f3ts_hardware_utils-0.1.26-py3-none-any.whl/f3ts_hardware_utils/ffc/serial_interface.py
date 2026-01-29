# !/usr/bin/env python
"""FixturFab Fixture Controller Board Interface."""
import logging
import re
from typing import Optional

import serial
from serial.tools import list_ports

__author__ = "M. Barnes / D. Wilkins"
__version__ = "1.2.0"
__email__ = "marzieh@fixturfab.com"

# """" Uncomment for logger output to console
logger = logging.getLogger(__name__)
logger.setLevel(
    logging.ERROR
)  # Adjust level as needed (DEBUG, INFO, WARNING, ERROR, etc.)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
# """


class FixturCNTLException(Exception):
    """Custom exception class for Fixture Controller errors."""

    pass


class FixturCNTL:
    """FixturFab Fixture Controller USB Hub Serial Interface."""

    def __init__(self, port=None, baud=57600, timeout=1):
        """Initialize Fixture Controller Serial Port Settings."""
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None

    def __del__(self):
        """Close hardware interfaces if object deleted."""
        self.close()

    def open(self):
        """Open serial port on FixturFab Fixture Controller.

        Raises:
            FixturCNTLException:
                If no matching device is found or if there's an error in connection.
        """
        try:
            if self.port:
                self._connect_to_port(self.port)
            else:
                self._auto_discover_and_connect()
        except IOError as e:
            raise FixturCNTLException(f"Failed to open Fixture Controller port: {e}")

    def close(self):
        """Close Fixture Controller USB Hub Serial Interface."""
        logger.debug("Closing fixture controller interface")
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.serial = None

    def _connect_to_port(self, port: str) -> None:
        """Connect to a specific port."""
        if self._is_fixturctl_board(port):
            logger.debug(
                f"Opening target serial interface port={self.port} (final binding)"
            )
            self.serial = serial.Serial(port, self.baud, timeout=self.timeout)

    def _auto_discover_and_connect(self) -> None:
        """Automatically discover and connect to a Fixture Controller device."""
        ports_list = list_ports.comports()
        pico_ports = [port for port, desc, hwid in ports_list if "2E8A:000A" in hwid]
        logger.debug(f"Found these possible serial ports in system {pico_ports}")

        fixturectl_ports = []
        for port in pico_ports:
            if self._is_fixturctl_board(port):
                fixturectl_ports.append(port)

        if not fixturectl_ports:
            raise FixturCNTLException("No Fixture Controller devices found in system")
        if len(fixturectl_ports) > 1:
            logger.warning(
                "More than one Fixture Controller detected in system"
                + {fixturectl_ports}
            )

        self.port = fixturectl_ports[0]  # Connect to first one
        logger.debug(
            f"Opening target serial interface port={self.port} (final binding)"
        )
        self.serial = serial.Serial(self.port, self.baud, timeout=self.timeout)

    def _is_fixturctl_board(self, port) -> bool:
        """Check if the device at the given port is a Fixture Controller board."""
        logger.debug(f"Checking if device at port={port} is a Fixture Controller board")
        try:
            logger.debug(
                f"Opening target serial interface port={port} (to check mfg and mpn)"
            )
            self.serial = serial.Serial(port, self.baud, timeout=self.timeout)
            output = self.send_command("who", check_ok=False)
            self.serial.close()
            if "FixturFab / Fixture Controller" in output:
                logger.debug(
                    f"Device @ {self.serial.name} is a FixturFab Fixture Controller"
                )
                return True
            else:
                logger.debug(
                    f"Device @ {self.serial.name} is not a FixturFab Fixture Controller"
                )
                return False
        except serial.SerialException as e:
            raise FixturCNTLException(f"Serial communication error: {e}")
        except FixturCNTLException:
            logger.info("Serial device is not a FixturSSR board")
            self.close()
            return False

    def send_command(
        self, command_str: str = "", numlines: int = 1, check_ok: bool = True
    ):
        """
        Send Serial Command to Fixture Controller Interface.

        :param command_str: command string to send over serial, defaults to ""
        :type command_str: str, optional
        :param numlines: number of lines expected back, defaults to 1
        :type numlines: int, optional
        :param check_ok: True to return IOError from missing 'OK'
        from return string, defaults to True
        :type check_ok: bool, optional
        :return: return string sent back over serial interface
        :rtype: str
        """
        if not self.serial:
            raise FixturCNTLException(
                "No connected serial interface to Fixture Controller"
            )

        command_bytes = bytes(f"{command_str}\r", "utf-8")
        logger.debug(f"Sending command: {command_str}")
        self.serial.write(command_bytes)

        output = ""
        for i in range(numlines):
            line = self.serial.readline().decode("utf-8")
            output += f"{line}\r"

        if check_ok and "OK" not in output:
            raise FixturCNTLException("Command Error: ", output)

        return output.strip()

    def firmware_version(self):
        """
        Get Firmware Version.

        :return: Firmware version
        :rtype: str
        """
        output = self.send_command("who", check_ok=False)
        fw_str = re.findall(r"\((.*?)\)", output)[0]
        return fw_str.split(" ")[-1]

    def who(self) -> str:
        """Get the manufacturer string."""
        return self.send_command("who", check_ok=False)

    def usb_port_enable(self, state: bool = True, port: int = 1):
        """Enable USB Power and Data.

        :param state: True for port enable, defaults to True
        :type state: bool, optional
        :param port: port number (1-6), defaults to 1
        :type port: int, optional
        :return: serial command output
        :rtype: str
        """
        if state:
            onoff = "on"
        else:
            onoff = "off"

        output = self.send_command(f"usb {port} {onoff}")

        return output

    def usb_port_enable_all(self, state: bool = True):
        """Enable All USB Power and Data.

        :param state: True for port enable, defaults to True
        :type state: bool, optional
        :return: serial command output
        :rtype: str
        """
        if state:
            onoff = "on"
        else:
            onoff = "off"

        output = self.send_command(f"allusb {onoff}")

        return output

    def get_cycles(self, eeprom: int = 1):
        """Get I2C Cycle Counter.

        :param eeprom: eeprom device, defaults to 1
        :type eeprom: int, optional
        :return: Cycle count
        :rtype: int
        """
        output = self.send_command("cycles", numlines=4)
        counters = output.splitlines()
        counters = list(filter(None, counters))[1:]
        counts = [cycle.split(": ")[1] for cycle in counters]

        return int(counts[eeprom - 1])

    def zero_cycles(self, eeprom: int = 1):
        """Zero I2C Cycle Counters.

        :param eeprom: eeprom device, defaults to 1
        :type eeprom: int, optional
        """
        self.send_command(f"zero {eeprom}")

    def get_i2c_eeprom_devices(self):
        """Get I2c eeprom Device Configurations.

        :return: Device Data
        :rtype: json
        """
        output = self.send_command("eptest", numlines=5, check_ok=False)
        device_strs = output.split("EEPROM memory detected...")[1:]

        device_data = []
        for info in device_strs:
            properties = info.split("\r\n\r  - ")[1:]

            json = {}
            for prop in properties:
                json[prop.split(": ")[0].strip()] = prop.split(": ")[1].strip()
            device_data += [json]

        return device_data

    def get_fixture_closed(self):
        """Get Fixture Close Inductive Switch State.

        :return: True if fixture closed mode, False if open
        :rtype: bool
        """
        output = self.send_command("fixture", check_ok=False)

        if "Open" in output:
            return False
        elif "Closed" in output:
            return True
        else:
            raise AssertionError("Unknown Data Received: ", output)

    def set_gpio_mode(self, gpio: int = 21, mode: str = "in"):
        """Set GPIO Mode to Input or Output.

        :param gpio: GPIO pin, defaults to 21
        :type gpio: int, optional
        :param mode: 'in' for input mode, 'out' for output mode, defaults to "in"
        :type mode: str, optional
        """
        output = self.send_command(f"gptype {gpio} {mode}")
        print(output)

    def set_gpio_state(self, gpio: int = 21, state: bool = True):
        """Set GPIO State.

        :param gpio: GPIO pin, defaults to 21
        :type gpio: int, optional
        :param state: True for output high, False for output low,
        defaults to True
        :type state: bool, optional
        """
        if state:
            state_str = "high"
        else:
            state_str = "low"

        output = self.send_command(f"gpset {gpio} {state_str}")
        print(output)

    def set_gpio_state_all(self, state: bool = True):
        """Set all GPIO to state.

        :param state: True for output high, False for output low,
        defaults to True
        :type state: bool, optional
        """
        if state:
            state_str = "high"
        else:
            state_str = "low"

        output = self.send_command(f"gpall {state_str}")
        print(output)

    def get_gpio_state(self, gpio: int = 21):
        """Get Digital GPIO State.

        :param gpio: GPIO pin, defaults to 21
        :type gpio: int, optional
        :return: GPIO State
        :rtype: bool
        """
        output = self.send_command(f"gpget {gpio}", numlines=2, check_ok=False)

        if "high" in output:
            return True
        elif "low" in output:
            return False
        else:
            raise AssertionError("Unknown Data Received: ", output)

    def get_analog_state(self, aio: int = 0):
        """Get ADC State.

        :param aio: ADC pin, defaults to 0
        :type aio: int, optional
        :return: voltage (V)
        :rtype: float
        """
        output = self.send_command(f"anget {aio}", numlines=2)
        print(output)

        adc_reading = int(output.splitlines()[0])
        voltage = adc_reading * 3.3 / 4096  # 12 bit ADC 9 ENOB

        return voltage

    def rgb_enable(
        self,
        gpio_pin=0,
        led_str_len=1,
    ) -> None:
        """
        Enable 1-wire RGB LED interface on a particular GPIO pin.

        Must specify the length of the daisy-chained LED string.

        Args:
            gpio_pin: GPIO pin that LED string is attached 0-36 (int)
            led_str_len: Number of LEDs in daisy-chained string (int)

        Returns:
            None
        """
        self.send_command(f"rgb_enable {gpio_pin} {led_str_len}")

    def rgb_set_color(
        self,
        led=0,
        red=0,
        grn=0,
        blu=0,
    ) -> None:
        """
        Set the color on a particular LED in the RGB daisy-chain.

        Args:
            led: particular LED, starts with 0 (int)
            red: Red color intensity 0-255 (int)
            grn: Green color intensity 0-255 (int)
            blu: Blue color intensity 0-255 (int)

        Returns:
            None
        """
        self.send_command(f"rgb_set {led} {red} {grn} {blu}")

    def rgb_clear(
        self,
    ) -> None:
        """
        Turn off all LEDs in the RGB daisy-chain.

        Args:
            None

        Returns:
            None
        """
        self.send_command("rgb_clear")
