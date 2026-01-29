"""I2C GPIO Expander Modules."""

import logging
from collections.abc import Iterable

import bitstring as bs
from usb_iss import UsbIss

import brainstem
from f3ts_hardware_utils.hw_modules import bit_read, bit_write
from f3ts_hardware_utils.mtm_utils import mtm_exec

logger = logging.getLogger(__name__)


class I2CWrapper(object):
    def __init__(self, i2c_bus):
        """
        Initialize the connection to the chip and set the a configuration if given.

        address: int
            integer of the I2C address of the TCA9555 (default is 0x20 e.g. 32)
        config: dict
            dictionary holding register values which should be set
        """
        # I2C-bus address; 0x20 (32 in decimal) if all address pins A0=A1=A2 are low
        self.i2c_bus = i2c_bus
        print("I2C Bus Type: ", type(self.i2c_bus))

    def write(self, address, buffer):
        """
        Write data to the given address on the I2C Bus.

        :param address: Device address
        :type address: Any
        :param buffer: Bytes to write
        :type buffer: Any
        :return: None if successful, raises Exception if an exception occurs
        """
        if isinstance(self.i2c_bus, UsbIss):
            self.i2c_bus.i2c.write_ad0(address, buffer)
        elif isinstance(self.i2c_bus, brainstem.entity.I2C):
            mtm_exec(self.i2c_bus.write, address, buffer)
        else:
            raise TypeError("Unsupported I2C Bus Type!")

    def read(self, address, length=1):
        """
        Read data from the given address on the I2C Bus.

        :param address: Device address
        :type address: int
        :param length: Number of bytes to read
        :type length: int
        :return: read data
        :rtype: list
        """
        if isinstance(self.i2c_bus, UsbIss):
            data = self.i2c_bus.i2c.read_ad0(address, length)
        elif isinstance(self.i2c_bus, brainstem.entity.I2C):
            data = mtm_exec(self.i2c_bus.read, address, length)
        else:
            raise TypeError("Unsupported I2C Bus Type!")

        return data

    def device_scan(self, start_addr: int = 0x00, end_addr: int = 0xFF):
        devices = []
        for addr in range(start_addr, end_addr):
            try:
                # Read register 0:
                self.write(addr, [0x00])
                self.read(addr, 1)
                devices += [hex(addr)]

            except Exception:
                continue

        return devices


class TCA9555(object):
    """
    TCA9555 Hardware Interface.

    This class implements an interface to the 16-bit IO expander using the
    I2C-interface of a Raspberry Pi

    The TCA9555 consists of two 8-bit Configuration (input or output selection),
    Input Port, Output Port and Polarity Inversion (active high or active low
    operation) registers which are also referred to as ports:
    Port 0 covers the IO bits P[7:0], port 1 covers bits P[15:8] (P[17:10]
    in datasheet convention). The bit representation of the bit states
    hardware-wise is big-endian:

        128 == 0b10000000 == bit 7 high, all others low
          1 == 0b00000001 == bit 0 high, all others low

    The default of representing the bit states within this class is to order
    by actual bit indices

        '10000000' ==  bit 0 high, all others low
        '00000001' == bit 7 high, all others low
    """

    # Internal registers of (port_0, port_1)
    regs = {
        # Registers holding the actual values of the pin levels
        "input": (0x00, 0x01),
        # Registers holding the target values of pin levels
        "output": (0x02, 0x03),
        # Registers holding the polarity (active-high or active-low)
        "polarity": (0x04, 0x05),
        # Registers holding whether the pins are configured as in- (1) or output (0)
        "config": (0x06, 0x07),
    }

    # Number of available io bits; bits are shared into ports
    _n_io_bits = 16

    # Number of bits of one port
    _n_bits_per_port = 8

    # Number of ports of TCA9555
    _n_ports = 2

    # Direction setting configurations
    OUTPUT = 0
    INPUT = 1

    # Polarity setting configurations
    DEFAULT = 0
    INVERTED = 1

    def __init__(self, i2c_bus, address: int = 0x20, config=None):
        """
        Initialize the connection to the chip and set the a configuration if given.

        address: int
            integer of the I2C address of the TCA9555 (default is 0x20 e.g. 32)
        config: dict
            dictionary holding register values which should be set
        """
        # I2C-bus address; 0x20 (32 in decimal) if all address pins A0=A1=A2 are low
        self.address = address
        self.i2c_bus = I2CWrapper(i2c_bus)
        print("I2C Bus Type: ", type(self.i2c_bus))

        if config:
            self.config = config

    @property
    def device_busy(self):
        """Check if Device is Busy."""
        return not self._device_available.is_set()

    @device_busy.setter
    def device_busy(self, val):
        """Set device_busy."""
        raise ValueError("This is a read-only property")

    @property
    def io_state(self):
        """Get IO Input State."""
        return self._get_state("input")

    @io_state.setter
    def io_state(self, state):
        """Set io_state."""
        self._set_state("output", state)

    @property
    def n_io_bits(self):
        """Get Number of IO Bits."""
        return self._n_io_bits

    @n_io_bits.setter
    def n_io_bits(self, val):
        """Set n_io_bits."""
        raise ValueError("This is a read-only property")

    @property
    def n_bits_per_port(self):
        """Get Number of Bits Per Port."""
        return self._n_bits_per_port

    @n_bits_per_port.setter
    def n_bits_per_port(self, val):
        """Set n_bits_per_port."""
        raise ValueError("This is a read-only property")

    @property
    def n_ports(self):
        """Number of Ports."""
        return self._n_ports

    @n_ports.setter
    def n_ports(self, val):
        """Set n_ports."""
        raise ValueError("This is a read-only property")

    @property
    def config(self):
        """Read Config Registers."""
        return {reg: self._get_state(reg) for reg in self.regs}

    @config.setter
    def config(self, config):
        """Set config."""
        for reg, val in config.items():
            self._set_state(reg, val)

    def _write(self, buffer):
        """
        Write a value to the MCP23017 I2C GPIO Expander.

        :param buffer: Bytes to write
        :type buffer: Any
        :return: None if successful, raises Exception if an exception occurs
        """
        self.i2c_bus.write(self.address, buffer)

    def _write_reg(self, register, data):
        """
        Write a value to the I2C GPIO Expander.

        :param length: Number of bytes to write
        :type length: int
        :param args: Bytes to write
        :return: None if successful, raises Exception if an exception occurs
        """
        self._write([register, data])

    def _read_reg(self, register, length=1):
        """
        Read a register from the I2C GPIO Expander.

        :param register: Register address to read
        :type register: int
        :param length: Number of bytes to read
        :type length: int
        :return: read data
        :rtype: list
        """
        self._write([register])
        return self.i2c_bus.read(self.address, length)

    def _create_state(self, state, bit_length):
        """
        Create a BitArray which represents the desired *state* of *bit_length* bits.

        Parameters
        ----------
        state: BitArray, int, str, Iterable
            state from which to create a BitArray
        bit_length: int
            length of the state
        """
        if isinstance(state, bs.BitArray):
            pass

        elif isinstance(state, int):
            state = bs.BitArray("uint:{}={}".format(bit_length, state))

        elif isinstance(state, Iterable):
            state = bs.BitArray(state)

        else:
            raise ValueError(
                "State must be integer, string or BitArray representing {} bits".format(
                    bit_length
                )
            )

        if len(state) != bit_length:
            raise ValueError("State must be {} bits".format(bit_length))

        return state

    def _check_register(self, reg):
        """
        Check if the register *reg* exists.

        Parameters
        ----------
        reg: str
            String of register name whose existence is checked
        """
        if reg not in self.regs:
            raise ValueError(
                "Register {} does not exist. Available registers: {}".format(
                    reg, ", ".join(self.regs.keys())
                )
            )

    def _check_bits(self, bits, val=None):
        """
        Check if the an operation on the IO bits is valid.

        Parameters
        ----------
        bits: int, Iterable of ints
            Iterable of bits on which an operation is performed
        val: int, None
            If not None, *val* must be an integer with bit length
            <= number of bits e.g. len(*bits*)
        """
        bits = bits if isinstance(bits, Iterable) else [bits]

        if any(not 0 <= b < self._n_io_bits for b in bits):
            raise IndexError(
                "{}'s {} bits are indexed from {} to {}".format(
                    self.__class__.__name__, self._n_io_bits, 0, self._n_io_bits - 1
                )
            )

        if len(set(bits)) != len(bits):
            raise IndexError(
                "Duplicate bit indices! *bits* must be composed of unique bit indices"
            )

        if val:
            if val.bit_length() > len(bits):
                raise ValueError(
                    "Too little bits. "
                    + "Bit length of value {} is {}, the number of bits is {}".format(
                        val, val.bit_length(), len(bits)
                    )
                )

        return bits

    def _set_bits(self, reg, val=1, bits=None):
        """
        Get the current state of an individual port of the TCA9555.

        Parameters
        ----------
        reg: str
            Name of register whose state will be read
        val: int, bool
            Either 0 or 1
        bits: Iterable, int
            bits to set to *val*
        """
        if val not in (0, 1, True, False):
            raise ValueError("'val' can only be 1 or 0")

        if bits is not None:
            # Check if bit indices and values are fine
            bits = self._check_bits(bits=bits)

            # Get current io configuration state
            state = self._get_state(reg=reg)

            # Loop over state and set bits
            for bit in bits:
                state[bit] = val

            # Set state
            self._set_state(reg, state)

        else:
            # Set all pins to *val*
            self._set_state(reg, [val] * self._n_io_bits)

    def _set_state(self, reg, state):
        """
        Set the *state* to the register *reg*.

        Parameters
        ----------
        reg: str
            Name of register whose state will be set
        state: BitString, Iterable, str
            Value from which a BitString-representation of *state* can be created
        """
        # Create empty target register state
        target_reg_state = self._create_state(state, self._n_io_bits)

        # loop over individual ports
        for port in range(self._n_ports):
            # Compare individual current port states with target port states
            start_bit = port * self._n_bits_per_port
            end_bit = (port + 1) * self._n_bits_per_port
            target_port_state = target_reg_state[start_bit:end_bit]

            # If target and current state differ, write
            if target_port_state != self._get_port_state(reg=reg, port=port):
                self._set_port_state(reg=reg, port=port, state=target_port_state)

    def _set_port_state(self, reg, port, state):
        """
        Get the current state of an individual port of the TCA9555.

        Parameters
        ----------
        reg: str
            Name of register whose state will be set
        port: int
            Index of the port; either 0 or 1
        state: BitString, Iterable, str, int
            Value from which a BitString-representation of *state* can be created
        """
        # Check if register exists
        self._check_register(reg)

        if port not in (0, 1):
            raise IndexError("*port* must be index of physical port; either 0 or 1")

        target_state = self._create_state(state=state, bit_length=self._n_bits_per_port)

        # Match bit order with physical pin order, increasing left to right
        target_state.reverse()

        self._write_reg(self.regs[reg][port], target_state.uint)

    def _get_state(self, reg):
        """
        Get the *state* to the register *reg*.

        Parameters
        ----------
        reg: str
            Name of register whose state will be read
        """
        state_sum = bs.BitArray(0)
        for port in range(self._n_ports):
            state = self._get_port_state(reg=reg, port=port)
            state_sum += state

        return state_sum

    def _get_port_state(self, reg, port):
        """
        Get the current state of an individual port of the TCA9555.

        Parameters
        ----------
        reg: str
            Name of register whose state will be read
        port: int
            Index of the port; either 0 or 1
        """
        # Check if register exists
        self._check_register(reg)

        if port not in (0, 1):
            raise IndexError("*port* must be index of physical port; either 0 or 1")

        # Read port state
        port_state = self._create_state(
            state=self._read_reg(self.regs[reg][port])[0],
            bit_length=self._n_bits_per_port,
        )

        # Match bit order with physical pin order, increasing left to right
        port_state.reverse()

        return port_state

    def int_to_bits(self, bits, val):
        """
        Set *bits* to state that represents *val*.

        Parameters
        ----------
        bits: Iterable, int
            bits which represent value *val*
        val: int
            Integer which should be represented though *bits* binary state
        """
        # Get the actual logic levels which are applied to the pins
        state = self._get_state("input")

        # Create state for set of bits
        val_bits = self._create_state(state=val, bit_length=len(bits))

        # Match bit order with physical pin order, increasing left to right
        val_bits.reverse()

        # Update current io state
        for i, bit in enumerate(bits):
            state[bit] = val_bits[i]

        # Set the updated state
        self._set_state("output", state)

    def int_from_bits(self, bits):
        """
        Get binary value from a set of *bits*.

        Parameters
        ----------
        bits: Iterable, int
            bits from which to read the integer
        """
        # Get the actual logic levels which are applied to the pins
        state = self.io_state

        # Read the respective bit values
        val_bits = bs.BitArray([state[bit] for bit in bits])

        # Match bit order with physical pin order, increasing left to right
        val_bits.reverse()

        return val_bits.uint

    def set_state(self, reg, state):
        """
        Thread-safe version of the private *_set_state*-method.

        Parameters
        ----------
        reg: str
            Name of register whose state will be set
        state: BitString, Iterable, str
            Value from which a BitString-representation of *state* can be created
        """
        self._set_state(reg=reg, state=state)

    def set_port_state(self, reg, port, state):
        """
        Thread-safe version of the private *_set_port_state*-method.

        Parameters
        ----------
        reg: str
            Name of register whose state will be set
        port: int
            Index of the port; either 0 or 1
        state: BitString, Iterable, str, int
            Value from which a BitString-representation of *state* can be created
        """
        self._set_port_state(reg=reg, port=port, state=state)

    def get_state(self, reg):
        """
        Thread-safe version of the private *_get_state*-method.

        Parameters
        ----------
        reg: str
            Name of register whose state will be read
        """
        self._get_state(reg=reg)

    def get_port_state(self, reg, port):
        """
        Thread-safe version of the private *_get_port_state*-method.

        Parameters
        ----------
        reg: str
            Name of register whose state will be read
        port: int
            Index of the port; either 0 or 1
        """
        self._get_port_state(reg=reg, port=port)

    def is_high(self, bit):
        """
        Get logical state of single bit.

        Parameters
        ----------
        bit: int
            bit from which to read the state
        """
        self._check_bits(bits=bit)

        return self.io_state[bit]

    def set_direction(self, direction, bits=None):
        """
        Set direction of bits: input (1) or output (0).

        Parameters
        ----------
        direction: int
            1 for input, 0 for output
        bits: Iterable, int, None
            bits for which the direction will be set
        """
        self._set_bits(reg="config", val=int(bool(direction)), bits=bits)

    def set_polarity(self, polarity, bits=None):
        """
        Set polarity of bits: active-high (0) or active-low (1).

        Parameters
        ----------
        polarity: int
            1 for inversion, 0 for default
        bits: Iterable, int, None
            bits for which the polarity will be set
        """
        self._set_bits(reg="polarity", val=int(bool(polarity)), bits=bits)

    def set_level(self, level, bits=None):
        """
        Convenience-method to set logic-level of bits.

        Parameters
        ----------
        level: int
            1 for logical high, 0 for logic 0
        bits: Iterable, int, None
            bits for which the level will be set
        """
        self._set_bits(reg="output", val=int(bool(level)), bits=bits)

    def get_level(self):
        """
        Convenience-method to get logic-level of bits.
        """
        return self._get_state(reg="input")

    def format_config(self, format_="bin"):
        """
        Return a more readable version of self.config.

        Parameters
        ----------
        format_: str
            Any attribute of BitArray-class
        """
        return {reg: getattr(state, format_) for reg, state in self.config.items()}

    def set_bits(self, bits=None):
        """
        Set bits e.g. set the output level to logical 1.

        Parameters
        ----------
        bits: Iterable, int, None
            bits of *reg* which will be set (to 1)
        """
        self.set_level(level=1, bits=bits)

    def unset_bits(self, bits=None):
        """
        Unset *bits* e.g. set the output level to logical 0.

        Parameters
        ----------
        bits: Iterable, int, None
            bits of *reg* which will be unset (to 0)
        """
        self.set_level(level=0, bits=bits)


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

    def _write(self, buffer):
        """
        Write a value to the MCP23017 I2C GPIO Expander.

        :param buffer: bytes to write
        :type buffer: Any
        :return: None if successful, raises Exception if an exception occurs
        """
        mtm_exec(self.i2c_bus.write, self.address, buffer)

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
        self._write([register])
        return mtm_exec(self.i2c_bus.read, self.address, length)

    def set_pin_modes(self, mode):
        """
        Set the mode for all pins masked pins.

        A 1 configures the pin as an input, a 0 configures the pin as an output

        :param mode: Mode to set pin to
        :type mode: int
        """
        self._write([self._IODIRA, mode & 0x00FF])
        self._write([self._IODIRB, (mode & 0xFF00) >> 8])

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
        self._write([self._GPPUA, (mask & 0x00FF)])
        self._write([self._GPPUB, (mask & 0xFF00) >> 8])

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
        self._write([self._GPIOA, (value & 0x00FF)])
        self._write([self._GPIOB, (value & 0xFF00) >> 8])

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
        self.i2c_bus = I2CWrapper(i2c_bus)
        self.address = address
        print(type(self.i2c_bus))

    def _write(self, byte_list):
        """
        Write a value to the MCP23017 I2C GPIO Expander.

        :param args: Bytes to write
        :return: None if successful, raises Exception if an exception occurs
        """
        self.i2c_bus.write(self.address, byte_list)

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
        self._write([register])
        return self.i2c_bus.read(self.address, length)

    def set_pin_modes(self, mode):
        """
        Set the mode for all pins masked pins.

        A 1 configures the pin as an input, a 0 configures the pin as an output

        :param mode: Mode to set pin to
        :type mode: int
        """
        modes = 0x00
        if mode:
            modes = 0xFF
        self._write([self._IODIR, modes])

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
        self._write([self._GPPU, (mask & 0x00FF)])

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
        self._write([self._GPIO, (value & 0x00FF)])

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
