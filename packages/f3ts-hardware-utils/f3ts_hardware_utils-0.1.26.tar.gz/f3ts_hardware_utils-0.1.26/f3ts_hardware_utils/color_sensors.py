"""Color Sensor Drivers."""
import logging

from f3ts_hardware_utils.mtm_utils import mtm_exec

__author__ = "Marzieh Barnes"
__version__ = "1.0.0"
__email__ = "marzieh@fixturfab.com"

logger = logging.getLogger(__name__)


class ISL29125:
    """ISL29125 Color Sensor Driver for Acroname MTM I2C."""

    # ISL29125 I2C Address
    ISL_I2C_ADDR = 0x88

    # ISL29125 Registers
    DEVICE_ID = 0x00
    CONFIG_1 = 0x01
    CONFIG_2 = 0x02
    CONFIG_3 = 0x03
    THRESHOLD_LL = 0x04
    THRESHOLD_LH = 0x05
    THRESHOLD_HL = 0x06
    THRESHOLD_HH = 0x07
    STATUS = 0x08
    GREEN_L = 0x09
    GREEN_H = 0x0A
    RED_L = 0x0B
    RED_H = 0x0C
    BLUE_L = 0x0D
    BLUE_H = 0x0E

    # Configuration Settings
    CFG_DEFAULT = 0x00

    # CONFIG1
    # Pick a mode, determines what color[s] the sensor samples, if any
    CFG1_MODE_POWERDOWN = 0x00
    CFG1_MODE_G = 0x01
    CFG1_MODE_R = 0x02
    CFG1_MODE_B = 0x03
    CFG1_MODE_STANDBY = 0x04
    CFG1_MODE_RGB = 0x05
    CFG1_MODE_RG = 0x06
    CFG1_MODE_GB = 0x07

    # Light intensity range
    # In a dark environment 375Lux is best, otherwise 10KLux is likely the best option
    CFG1_375LUX = 0x00
    CFG1_10KLUX = 0x08

    # Change this to 12 bit if you want less accuracy, but faster sensor reads
    # At default 16 bit, each sensor sample for a given color is about ~100ms
    CFG1_16BIT = 0x00
    CFG1_12BIT = 0x10

    # Unless you want the interrupt pin to be an input that triggers sensor sampling,
    # leave this on normal
    CFG1_ADC_SYNC_NORMAL = 0x00
    CFG1_ADC_SYNC_TO_INT = 0x20

    # CONFIG2
    # Selects upper or lower range of IR filtering
    CFG2_IR_OFFSET_OFF = 0x00
    CFG2_IR_OFFSET_ON = 0x80

    # Sets amount of IR filtering, can use these presets or any value between = 0x00
    # and = 0x3F
    # Consult datasheet for detailed IR filtering calibration
    CFG2_IR_ADJUST_LOW = 0x00
    CFG2_IR_ADJUST_MID = 0x20
    CFG2_IR_ADJUST_HIGH = 0x3F

    # CONFIG3
    # No interrupts, or interrupts based on a selected color
    CFG3_NO_INT = 0x00
    CFG3_G_INT = 0x01
    CFG3_R_INT = 0x02
    CFG3_B_INT = 0x03

    # How many times a sensor sample must hit a threshold before triggering an interrupt
    # More consecutive samples means more times between interrupts, but less triggers
    # from short transients
    CFG3_INT_PRST1 = 0x00
    CFG3_INT_PRST2 = 0x04
    CFG3_INT_PRST4 = 0x08
    CFG3_INT_PRST8 = 0x0C

    # If you would rather have interrupts trigger when a sensor sampling is complete,
    # enable this. If this is disabled, interrupts are based on comparing sensor data
    # to threshold settings
    CFG3_RGB_CONV_TO_INT_DISABLE = 0x00
    CFG3_RGB_CONV_TO_INT_ENABLE = 0x10

    # STATUS FLAG MASKS
    FLAG_INT = 0x01
    FLAG_CONV_DONE = 0x02
    FLAG_BROWNOUT = 0x04
    FLAG_CONV_G = 0x10
    FLAG_CONV_R = 0x20
    FLAG_CONV_B = 0x30

    def __init__(self, usb_stem):
        """Initialize I2C Interface."""
        # usb_stem = brainstem.stem.MTMUSBStem()
        self.i2c = usb_stem.i2c[1]
        mtm_exec(self.i2c.setSpeed, self.i2c.I2C_SPEED_100Khz)
        mtm_exec(self.i2c.setPullup, True)

        devID = self.read8(self.DEVICE_ID)
        if devID.hex() != "7d":
            raise AssertionError(f"Device ID: {devID}, Expected: 7D")

        self.reset()

        CFG1 = self.CFG1_MODE_RGB | self.CFG1_10KLUX
        self.config(CFG1, self.CFG2_IR_ADJUST_HIGH, self.CFG_DEFAULT)

        self.resolution = 10000 / 65536

    def read8(self, register):
        """Read register of size 1 byte."""
        mtm_exec(self.i2c.write, self.ISL_I2C_ADDR, 1, register)
        data = mtm_exec(self.i2c.read, self.ISL_I2C_ADDR, 1)

        return data

    def write8(self, register, data):
        """Write register of size 1 byte."""
        mtm_exec(self.i2c.write, self.ISL_I2C_ADDR, 2, [register, data])

    def reset(self):
        """Reset Configuration Registers."""
        self.write8(self.DEVICE_ID, 0x46)

        data = self.read8(self.CONFIG_1).hex()
        data += self.read8(self.CONFIG_2).hex()
        data += self.read8(self.CONFIG_3).hex()
        data += self.read8(self.STATUS).hex()
        if int(data, 16) != 0:
            raise AssertionError(f"Unable to Reset Configuration registers: {data}")

    def config(self, config1, config2, config3):
        """Set Configuration Registers."""
        self.write8(self.CONFIG_1, config1)
        data = int(self.read8(self.CONFIG_1).hex(), 16)
        if data != config1:
            raise AssertionError(
                f"Unable to Set Configuration Register {self.CONFIG_1} to {config1}:"
                + f"Data read at at config register: {data}"
            )

        self.write8(self.CONFIG_2, config2)
        data = int(self.read8(self.CONFIG_2).hex(), 16)
        if data != config2:
            raise AssertionError(
                f"Unable to Set Configuration Register {self.CONFIG_2} to {config2}:"
                + f"Data read at at config register: {data}"
            )

        self.write8(self.CONFIG_3, config3)
        data = int(self.read8(self.CONFIG_3).hex(), 16)
        if data != config3:
            raise AssertionError(
                f"Unable to Set Configuration Register {self.CONFIG_3} to {config3}:"
                + f"Data read at at config register: {data}"
            )

    def readRed(self):
        """Get red illuminance in lux."""
        low = self.read8(self.RED_L).hex()
        high = self.read8(self.RED_H).hex()
        return int((high + low), 16) * self.resolution  # units of lux

    def readGreen(self):
        """Get green illuminance in lux."""
        low = self.read8(self.GREEN_L).hex()
        high = self.read8(self.GREEN_H).hex()
        return int((high + low), 16) * self.resolution  # units of lux

    def readBlue(self):
        """Get blue illuminance in lux."""
        low = self.read8(self.BLUE_L).hex()
        high = self.read8(self.BLUE_H).hex()
        return int((high + low), 16) * self.resolution  # units of lux
