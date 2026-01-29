# !/usr/bin/env python
"""FixturFab FixturIO Controller Board Interface."""

import logging
import statistics
from typing import List, Optional

import serial
from serial.tools import list_ports

__author__ = "D. Wilkins"
__version__ = "1.0.0"
__email__ = "dave@fixturfab.com"

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


class FixturIOException(Exception):
    """Custom exception class for FixturIO errors."""

    pass


class FixturIO:
    """FixturIO Controller Serial Interface."""

    def __init__(
        self,
        port: str = "",
        baud: int = 57600,
        timeout: int = 1,
        card_id: Optional[int] = None,
    ):
        """Initialize Serial Configurations."""
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None
        self.card_id = card_id

    def __del__(self):
        """Close interface if object is deleted."""
        self.close()

    # ##################################################################################
    # Serial Discovery & Connection
    # ##################################################################################

    def open(self) -> None:
        """
        Open serial port on FixturFab FixturIO Controller.

        Raises:
            FixturIOException: If no matching FixturIO device is found
            or if there's an error in connection.
        """
        # Get the OS type to manage serial interface naming conventions
        try:
            if self.port:
                self._connect_to_port(self.port)
            else:
                self._auto_discover_and_connect()
        except IOError as e:
            raise FixturIOException(f"Failed to open FixturIO port: {e}")

    def close(self) -> None:
        """Close the FixturIO Controller serial interface."""
        if self.serial and self.serial.is_open:
            logger.debug("Closing FixturIO Controller interface")
            self.serial.close()
            self.serial = None

    def list_ports(self) -> List[str]:
        """Return a list of FixturIO serial ports ennumerated in system."""
        logger.info(
            "Looking for all serial ports in system with USB VID:PID = [16C0:0483]"
        )
        ports_list = list_ports.comports()
        teensy_ports = [port for port, desc, hwid in ports_list if "16C0:0483" in hwid]
        logger.debug(f"Found these possible serial ports in system {teensy_ports}")
        fixturio_ports = []
        for port in teensy_ports:
            if self._is_fixturio_board(port):
                fixturio_ports.append(port)
        return fixturio_ports

    def _connect_to_port(self, port: str) -> None:
        """Connect to a specific port."""
        if self._is_fixturio_board(port):
            logger.debug(f"Opening FixturIO Controller interface port={port}")
            self.serial = serial.Serial(port, self.baud, timeout=self.timeout)
            if self.card_id is not None:
                logger.debug(f"Checking card_id={self.card_id} @ port={port}")
                if self.card_identifier() != self.card_id:
                    raise FixturIOException(
                        f"Found FixturIO device at port={self.port} "
                        + f"but doesn't match specified card_id={self.card_id}"
                    )
            self.port = port
        else:
            raise FixturIOException(f"Resource at port={port} is not a FixturIO card")

    def _auto_discover_and_connect(self) -> None:
        """Automatically discover and connect to a FixturIO device."""
        fixturio_ports = self.list_ports()
        card_id_match = []

        if not fixturio_ports:
            raise FixturIOException("No FixturIO devices found in system")
        if len(fixturio_ports) > 1 and self.card_id is None:
            raise FixturIOException(
                f"{len(fixturio_ports)} FixturIO devices found in system, "
                + "use port or card_id to differentiate devices"
            )

        for port in fixturio_ports:
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
            raise FixturIOException(
                f"No FixturIO devices found in system with card_id = {self.card_id}"
            )

        if len(card_id_match) > 1:  # Too many card_id matches, can't differentiate
            raise FixturIOException(
                f"More than one FixurIO device with card_id = {self.card_id}, "
                + "cannot differentiate"
            )

        self.port = card_id_match[0]  # Must be a list of one port
        logger.debug(
            f"Opening target serial interface port={self.port} (final binding)"
        )
        self.serial = serial.Serial(self.port, self.baud, timeout=self.timeout)

    def _is_fixturio_board(self, port: str) -> bool:
        """Check if the device at the given port is a FixturIO board."""
        logger.debug(f"Checking if device at port={port} is a FixturIO board")
        try:
            logger.debug(
                f"Opening target serial interface port={port}"
                + "(to check mfg and part_number)"
            )
            self.serial = serial.Serial(port, self.baud, timeout=self.timeout)
            is_fixturio = (
                "FixturFab" in self.manufacturer() and "101-0339-" in self.part_number()
            )
            self.close()
            return is_fixturio
        except serial.SerialException:
            # raise FixturIOException(f"Serial communication error: {e}")
            # Device is likely not available for connection (i.e. already connected to something else)
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
        """Rest and close interface."""
        self.set_command("reset")
        self.close()

    # ##################################################################################
    # Console Commands / Returns
    # ##################################################################################

    def set_command(self, command_str: str) -> None:
        """
        Send a serial command to the FixturIO Controller.

        Check for acknowledgment,no response expected.
        """
        if not self.serial:
            raise FixturIOException(
                "set_command: Not connected to FixturIO Controller serial interface"
            )
        self._send_command(command_str)
        status = self._read_line()
        if "OK" not in status:
            raise FixturIOException(f"Command '{command_str}' failed: {status}")

    def get_command(self, command_str: str) -> str:
        """
        Send a serial command to query the FixturIO Controller.

        Check for acknowledgement, return the response.
        """
        if not self.serial:
            raise FixturIOException(
                "get_command: Not connected to FixturIO Controller serial interface"
            )
        self._send_command(command_str)
        output = self._read_line()
        if "KO -" in output:
            raise FixturIOException(f"Command '{command_str}' failed: {output}")
        status = self._read_line()
        if "OK" not in status:
            raise FixturIOException(f"Command '{command_str}' failed: {output}")
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
    # GPIO
    # ##################################################################################

    def set_gpio_mode(self, gpio: int = 0, mode: str = "in") -> None:
        """Set the pin mode of a particular GPIO.

        GPIO modes:
        / out = an output
        / in = an input (required for ADC functions)
        / inpu = an input with a weak pull-up resistor
        / inpd = an input with a weak pull-down resistor.
        Note: after reset or power-up the FixturIO pins are all set
        to input orientation with a weak pull-down resistor.

        Args:
            gpio: GPIO Pin# 0-36 (int)
            mode: GPIO Mode "out"|"in"|"inpu"|"inpd" (str)

        Returns:
            None
        """
        self.set_command(f"iotype {gpio} {mode}")

    def set_gpio_state(self, gpio: int = 0, state: int = 0) -> None:
        """
        Set the state of a particular GPIO pin.

        Pins set to high (1) or low (0) if it is defined as an output

        Args:
            gpio: GPIO Pin#0-36 (int)
            state: GPIO State 1|0 (int)

        Returns:
            None
        """
        self.set_command(f"ioset {gpio} {state}")

    def set_gpio_state_all(self, state: int = 0) -> None:
        """
        Set the state of all GPIO pins that are defined.

        Pins as outputs to be high (1) or low (0)

        Args:
            state: GPIO State 1|0 (int)

        Returns:
            None
        """
        self.set_command(f"ioall {state}")

    def get_gpio_state(self, gpio: int = 0) -> int:
        """
        Get the current state of a particular GPIO pin.

        Args:
            gpio: GPIO Pin# 0-36 (int)

        Returns:
            State of pin: 1|0 (int)
        """
        output = self.get_command(f"ioget {gpio}")
        return int(output)

    def get_analog_value(self, aio: int = 0, average: int = 1) -> int:
        """
        Perform and retrieve a 12-bit ADC reading on a particular GPIO pin.

        Args:
            aio: Analog Pin# 0-15 (int)
            average: average over this number of successive readings (int)

        Returns:
            Decimal ADC reading (int)
        """
        assert aio >= 0 and aio <= 15, "Mux channel must be 0-15"
        assert average >= 1, "Argument for reading average must be >=1"
        adc = []
        for i in range(average):
            adc.append(int(self.get_command(f"adc {aio}")))
        return int(round(statistics.mean(adc)))

    def get_analog_voltage(self, aio: int = 0, average: int = 1) -> float:
        """
        Perform and retrieve a 12-bit ADC reading on GPIO pin.

        Converted to Voltage units.

        Args:
            aio: Analog Pin# 0-15 (int)
            average: average over this number of successive readings (int)

        Returns:
            One or more ASCII characters representing the Voltage reading (float)
        """
        assert aio >= 0 and aio <= 15, "Mux channel must be 0-15"
        assert average >= 1, "Argument for reading average must be >=1"
        adc = []
        for i in range(average):
            adc.append(int(self.get_command(f"adc {aio}")))
        voltage = statistics.mean(adc) * 3.3 / 4095  # 12-bit ADC to Volts
        return voltage

    # ##################################################################################
    # I2C Interfaces
    # ##################################################################################

    I2C_CLK_100KHz = "standard"
    I2C_CLK_400KHz = "fast"
    I2C_CLK_1MHz = "fast+"

    def i2c_enable(self, bus_num: int = 0) -> None:
        """
        Enable a particular I2C bus on FixturIO Controller.

        Note, associated pins will no longer be available as GPIO resources.

        Args:
            bus_number: I2C bus identifier 0-2 (int)

        Returns:
            None
        """
        self.set_command(f"i2c_cntl {bus_num} enable")

    def i2c_speed(self, bus_num: int = 0, clk_speed: str = I2C_CLK_100KHz) -> None:
        """
        Enable a particular I2C bus on FixturIO Controller.

        Note, associated pins will no longer be available as GPIO resources.

        Args:
            bus_number: I2C bus identifier 0-2 (int)

        Returns:
            None
        """
        self.set_command(f"i2c_clk {bus_num} {clk_speed}")

    def i2c_hello(self, bus_num: int = 0, chip_addr: int = 1) -> int:
        """Poke I2C Bus to see if a device responds @ a particular address.

        Args:
            bus_number: I2C bus identifier 0-2 (int)
            chip_addr: Device's I2C address 1-127 (int)

        Returns:
            1 if a device responds at the address, 0 otherwise
        """
        return int(self.get_command(f"i2c_hello {bus_num} {chip_addr}"))

    def i2c_write(
        self,
        bus_num: int = 0,
        chip_addr: int = 1,
        reg_addr: int = 0,
        reg_size: int = 1,
        data: List[int] = 0,
    ) -> int:
        """
        Write data to I2C Bus device at a particular register address.

        Data is passed in as a list of integers representing bytes (0-255).

        Args:
            bus_number: I2C bus identifier 0-2 (int)
            chip_addr: Device's I2C address 1-127 (int)
            reg_addr: Device's register address (int)
            reg_size: Size of the register in bytes (int: 1|2|4)
            data: List of bytes to write (int: 0-255)

        Returns:
            1 if write operation successful, raises error otherwise
        """
        # Make sure we've been passed a list of data to write
        if not isinstance(data, list):
            raise FixturIOException(
                "FixturIO Controller i2c_write function data parameter "
                + "must be a list of integers representing bytes"
            )

        if not (reg_size == 1 or reg_size == 2 or reg_size == 4):
            raise FixturIOException(
                "FixturIO Controller i2c_write reg_size must be set "
                + "to 1, 2, or 4 bytes (i.e. byte, word, dword)"
            )

        for item in data:
            if reg_size == 1:
                if item >= 0 and item <= 255:  # 2^8 data scope
                    self.set_command(
                        f"i2c_write {bus_num} {chip_addr} {reg_addr} {reg_size} {item:02x}"
                    )
                else:
                    raise FixturIOException(
                        "i2c_write data size is incompatible with reg_size setting (0-255)"
                    )
            if reg_size == 2:
                if item >= 0 and item <= 65535:  # 2^16 data scope
                    self.set_command(
                        f"i2c_write {bus_num} {chip_addr} {reg_addr} {reg_size} {item:04x}"
                    )
                else:
                    raise FixturIOException(
                        "i2c_write data size is incompatible with reg_size setting (0 to 65535)"
                    )
            if reg_size == 4:
                if item >= 0 and item <= 4294967295:  # 2^32 data scope
                    self.set_command(
                        f"i2c_write {bus_num} {chip_addr} {reg_addr} {reg_size} {item:08x}"
                    )
                else:
                    raise FixturIOException(
                        "i2c_write data size is incompatible with reg_size setting (0 to 4294967295)"
                    )
            reg_addr += 1

        return 1

    def i2c_read(
        self,
        bus_num: int = 0,
        chip_addr: int = 1,
        reg_addr: int = 0,
        reg_size: int = 1,
        num_reg: int = 1,
    ) -> List[int]:
        """
        Read data from I2C Bus device at a particular register address.

        Data is returned as a list of integers representing bytes (0-255).

        Args:
            bus_number: I2C bus identifier 0-2 (int)
            chip_addr: Device's I2C address 1-127 (int)
            reg_addr: Device's register address (int)
            reg_size: Size of the register in bytes 1|2|4 (int)
            num_reg: Number of registers to fetch (int)

        Returns:
            List of registers read (int)
        """
        data = []

        for offset in range(num_reg):
            output = self.get_command(
                f"i2c_read {bus_num} {chip_addr} {reg_addr+offset} {reg_size}"
            )
            if not (output):
                raise FixturIOException(
                    "FixturIO Controller i2c_read function returned failed status"
                )

            data.append(int(output, 16))

        return data

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
        self.set_command(f"rgb_enable {gpio_pin} {led_str_len}")

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
        self.set_command(f"rgb_set {led} {red} {grn} {blu}")

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
        self.set_command("rgb_clear")
