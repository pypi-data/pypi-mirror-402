"""MCP GPIO Expander Modules."""
import logging

from .mtm_utils import mtm_exec

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Bit Write Functions
# -----------------------------------------------------------------------------


def bit_read(value, bit):
    """
    Read a bit from a value.

    :param value: Value to get bit from
    :type value: int
    :param bit: Bit number to read
    :type bit: int
    :return: Value of the specified bit
    :rtype: int
    """
    return (value >> bit) & 0x01


def bit_set(value, bit):
    """
    Set a bit in a value.

    :param value: Value to set bit in
    :type value: int
    :param bit: Bit number to set
    :type bit: int
    :return: Updated value with the specified bit set
    :rtype: int
    """
    return value | (1 << bit)


def bit_clear(value, bit):
    """
    Clear a bit in a value.

    :param value: Value to clear bit in
    :type value: int
    :param bit: Bit number to set
    :type bit: int
    :return: Updated value with the specified bit cleared
    :rtype: int
    """
    return value & ~(1 << bit)


def bit_write(value, bit, bit_value):
    """
    Write a bit in a value.

    :param value: Value to write bit in
    :type value: int
    :param bit: Bit number to set
    :type bit: int
    :param bit_value: Value to set bit to (0 or 1)
    :type bit_value: int
    :return: Updated value
    :rtype: int
    """
    if bit_value:
        return bit_set(value, bit)
    else:
        return bit_clear(value, bit)


class MCP23017(object):
    """MCP23017 I2C GPIO Expander."""

    INPUT = 1
    OUTPUT = 0

    # MCP23017 Registers
    _IODIR = 0x00
    _IODIRA = 0x00
    _IODIRB = 0x01
    _IOPOL = 0x01
    _IPOLA = 0x02
    _IPOLB = 0x03
    _GPINTEN = 0x02
    _GPINTENA = 0x04
    _GPINTENB = 0x05
    _DEFVAL = 0x03
    _DEFVALA = 0x06
    _DEFVALB = 0x07
    _INTCON = 0x04
    _INTCONA = 0x08
    _INTCONB = 0x09
    _IOCON = 0x05
    _IOCONA = 0x0A
    _IOCONB = 0x0B
    _GPPU = 0x06
    _GPPUA = 0x0C
    _GPPUB = 0x0D
    _INTF = 0x07
    _INTFA = 0x0E
    _INTFB = 0x0F
    _INTCAP = 0x08
    _INTCAPA = 0x10
    _INTCAPB = 0x11
    _GPIO = 0x09
    _GPIOA = 0x12
    _GPIOB = 0x13
    _OLAT = 0x0A
    _OLATA = 0x14
    _OLATB = 0x15

    def __init__(self, i2c_bus, address=0x40):
        """Initialize the I2C Bus."""
        self.i2c_bus = i2c_bus
        self.address = address

    def _write(self, length, *args):
        """
        Write a value to the MCP23017 I2C GPIO Expander.

        :param length: Number of bytes to write
        :type length: int
        :param args: Bytes to write
        :return: None if successful, raises Exception if an exception occurs
        """
        mtm_exec(self.i2c_bus.write, self.address, length, *args)

    def _read(self, register, length=1):
        """
        Read a register from the MCP23017 I2C GPIO Expander.

        :param register: Register address to read
        :type register: int
        :param length: Number of bytes to read
        :type length: int
        :return: read data
        :rtype: list
        """
        self._write(1, register)
        return mtm_exec(self.i2c_bus.read, self.address, length)

    def set_pin_modes(self, mode):
        """
        Set the mode for all pins masked pins.

        A 1 configures the pin as an input, a 0 configures the pin as an output

        :param mode: Mode to set pin to
        :type mode: int
        """
        self._write(2, self._IODIRA, mode & 0x00FF)
        self._write(2, self._IODIRB, (mode & 0xFF00) >> 8)

    def get_pin_modes(self):
        """
        Get the current pin modes.

        :return: current pin modes
        :rtype: int
        """
        data = self._read(self._IODIRA, 2)
        return (data[1] << 8) + data[0]

    def set_pin_mode(self, pin, mode):
        """
        Set the mode of the specified pin.

        A 1 configures the pin as an input, a 0 configures the pin as an output

        :param pin: Pin to set mode for
        :type pin: int
        :param mode: Mode to set pin to
        :type mode: int
        """
        cur_modes = self.get_pin_modes()
        self.set_pin_modes(bit_write(cur_modes, pin, mode))

    def get_pin_mode(self, pin):
        """
        Get the mode of the specified pin.

        :param pin: Pin number to get mode for
        :type pin: int
        :return: Pin mode
        :rtype: int
        """
        cur_modes = self.get_pin_modes()
        return bit_read(cur_modes, pin)

    def get_pullups(self):
        """
        Read current pull-up register states.

        :return: Register states
        :rtype: int
        """
        data = self._read(self._GPPUA, 2)
        return (data[1] << 8) + data[0]

    def set_pullups(self, mask):
        """
        Enable/Disable pullups.

        Enable or disable the pullups on each channel. A 1 will enable the
        internal pullup and a 0 will disable it. The internal pullups are
        100kOhm.

        :param mask: Pullups to enable/disable
        :type mask: int
        """
        self._write(2, self._GPPUA, (mask & 0x00FF))
        self._write(2, self._GPPUB, (mask & 0xFF00) >> 8)

    def set_pullup(self, pin, mode):
        """
        Enable/Disable pullups for a pin.

        :param pin: Pin to set pullup state
        :type pin: int
        :param mode: Enable/Disable pin
        :type mode: bool
        """
        cur_modes = self.get_pullups()
        logger.debug(f"set_pullup: cur_modes={cur_modes}")
        self.set_pullups(bit_write(cur_modes, pin, mode))

    def set_pins(self, value):
        """
        Set the pin states.

        :param value: Value to write to all 16-pins
        :type value: int
        """
        self._write(2, self._GPIOA, (value & 0x00FF))
        self._write(2, self._GPIOB, (value & 0xFF00) >> 8)

    def get_pins(self):
        """
        Get the pin states.

        :return: Pin States
        :rtype: int
        """
        data = self._read(self._GPIOA, 2)
        return (data[1] << 8) + data[0]

    def set_pin(self, pin, value):
        """
        Set the value of a pin.

        :param pin: Pin to set value for
        :type pin: int
        :param value: Value to set
        :type value: int
        """
        cur_states = self.get_pins()
        self.set_pins(bit_write(cur_states, pin, value))

    def get_pin(self, pin):
        """
        Get the value of a pin.

        :param pin: Pin to get value for
        :type pin: int
        :return: Value of the specified pin
        :rtype: int
        """
        cur_states = self.get_pins()
        return bit_read(cur_states, pin)


class MCP23008(object):
    """MCP23008 I2C GPIO Expander."""

    INPUT = 1
    OUTPUT = 0

    # MCP23017 Registers
    _IODIR = 0x00
    _IOPOL = 0x01
    _GPINTEN = 0x02
    _DEFVAL = 0x03
    _INTCON = 0x04
    _IOCON = 0x05
    _GPPU = 0x06
    _INTF = 0x07
    _INTCAP = 0x08
    _GPIO = 0x09
    _OLAT = 0x0A

    def __init__(self, i2c_bus, address=0x40):
        """Initialize the I2C Bus."""
        self.i2c_bus = i2c_bus
        self.address = address

    def _write(self, length, *args):
        """
        Write a value to the MCP23017 I2C GPIO Expander.

        :param length: Number of bytes to write
        :type length: int
        :param args: Bytes to write
        :return: None if successful, raises Exception if an exception occurs
        """
        mtm_exec(self.i2c_bus.write, self.address, length, *args)

    def _read(self, register, length=1):
        """
        Read a register from the MCP23017 I2C GPIO Expander.

        :param register: Register address to read
        :type register: int
        :param length: Number of bytes to read
        :type length: int
        :return: read data
        :rtype: list
        """
        self._write(1, register)
        return mtm_exec(self.i2c_bus.read, self.address, length)

    def set_pin_modes(self, mode):
        """
        Set the mode for all pins masked pins.

        A 1 configures the pin as an input, a 0 configures the pin as an output

        :param mode: Mode to set pin to
        :type mode: int
        """
        self._write(2, self._IODIR, mode & 0x00FF)

    def get_pin_modes(self):
        """
        Get the current pin modes.

        :return: current pin modes
        :rtype: int
        """
        data = self._read(self._IODIR, 1)
        return data[0]

    def set_pin_mode(self, pin, mode):
        """
        Set the mode of the specified pin.

        A 1 configures the pin as an input, a 0 configures the pin as an output

        :param pin: Pin to set mode for
        :type pin: int
        :param mode: Mode to set pin to
        :type mode: int
        """
        cur_modes = self.get_pin_modes()
        self.set_pin_modes(bit_write(cur_modes, pin, mode))

    def get_pin_mode(self, pin):
        """
        Get the mode of the specified pin.

        :param pin: Pin number to get mode for
        :type pin: int
        :return: Pin mode
        :rtype: int
        """
        cur_modes = self.get_pin_modes()
        return bit_read(cur_modes, pin)

    def get_pullups(self):
        """
        Read current pull-up register states.

        :return: Register states
        :rtype: int
        """
        data = self._read(self._GPPU, 1)
        return data[0]

    def set_pullups(self, mask):
        """
        Enable/Disable pullups.

        Enable or disable the pullups on each channel. A 1 will enable the
        internal pullup and a 0 will disable it. The internal pullups are
        100kOhm.

        :param mask: Pullups to enable/disable
        :type mask: int
        """
        self._write(2, self._GPPU, (mask & 0x00FF))

    def set_pullup(self, pin, mode):
        """
        Enable/Disable pullups for a pin.

        :param pin: Pin to set pullup state
        :type pin: int
        :param mode: Enable/Disable pin
        :type mode: bool
        """
        cur_modes = self.get_pullups()
        logger.debug(f"set_pullup: cur_modes={cur_modes}")
        self.set_pullups(bit_write(cur_modes, pin, mode))

    def set_pins(self, value):
        """
        Set the pin states.

        :param value: Value to write to all 16-pins
        :type value: int
        """
        self._write(2, self._GPIO, (value & 0x00FF))

    def get_pins(self):
        """
        Get the pin states.

        :return: Pin States
        :rtype: int
        """
        data = self._read(self._GPIO, 1)
        return data[0]

    def set_pin(self, pin, value):
        """
        Set the value of a pin.

        :param pin: Pin to set value for
        :type pin: int
        :param value: Value to set
        :type value: int
        """
        cur_states = self.get_pins()
        self.set_pins(bit_write(cur_states, pin, value))

    def get_pin(self, pin):
        """
        Get the value of a pin.

        :param pin: Pin to get value for
        :type pin: int
        :return: Value of the specified pin
        :rtype: int
        """
        cur_states = self.get_pins()
        return bit_read(cur_states, pin)
