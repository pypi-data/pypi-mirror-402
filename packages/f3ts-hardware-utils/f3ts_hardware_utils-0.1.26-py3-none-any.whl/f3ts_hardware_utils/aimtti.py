"""
AimTTI Devices.

This module contains classes and functions for interfacing with AimTTI instrumentation
"""
import logging

import serial

logger = logging.getLogger(__name__)


class TF930(object):
    """
    TF930 Frequency Counter.

    This class controls a AimTTI TF930 Frequency Counter
    """

    def __init__(self, port):
        """Initialize TF930 Serial Interface."""
        logger.info(f"TF930: connecting to instrument on port={port}")
        self.ser = serial.Serial(baudrate=115200, port=port)

    def close(self):
        """Close connection to instrument."""
        logger.info("TF930: closing connection to instrument")
        self.ser.close()

    def write(self, cmd):
        """Write a command to the instrument."""
        self.ser.write(f"{cmd}\n".encode("utf-8"))

    def send_cmds(self, cmds):
        """Send a list of commands to the instrument."""
        self.write([f"{cmd};" for cmd in cmds][0:-1])

    def read(self):
        """Read the frequency in Hz."""
        return float(self.ser.readline().decode("utf-8").strip("\r\n")[:-2])

    def set_input_period_b(self):
        """Set input period to B channel."""
        self.write("F0")

    def set_input_period_a(self):
        """Set input period to A channel."""
        self.write("F1")

    def set_input_frequency_a(self):
        """Set input frequency to A channel."""
        self.write("F2")

    def set_input_frequency_b(self):
        """Set input frequency to B channel."""
        self.write("F3")

    def set_frequency_ratio_b_to_a(self):
        """Set frequency ratio to B/A."""
        self.write("F4")

    def set_a_input_width_high(self):
        """Set A input width high."""
        self.write("F5")

    def set_a_input_width_low(self):
        """Set A input width low."""
        self.write("F6")

    def set_a_input_count(self):
        """Set A input count."""
        self.write("F7")

    def set_a_input_ratio_h_to_l(self):
        """Set A input ratio high to low."""
        self.write("F8")

    def set_a_input_duty_cycle(self):
        """Set A input duty cycle."""
        self.write("F9")

    def set_a_input_ac_coupling(self):
        """Set A input AC coupling."""
        self.write("AC")

    def set_a_input_dc_coupling(self):
        """Set A input DC coupling."""
        self.write("DC")

    def set_a_input_hi_z(self):
        """Set A input high impedance."""
        self.write("Z1")

    def set_a_input_lo_z(self):
        """Set A input low impedance."""
        self.write("Z5")

    def set_a_input_1_to_1_atten(self):
        """Set A input 1 to 1 attenuation."""
        self.write("A1")

    def set_a_input_5_to_1_atten(self):
        """Set A input 5 to 1 attenuation."""
        self.write("A5")

    def set_rising_edge(self):
        """Set trigger to rising edge."""
        self.write("ER")

    def set_falling_edge(self):
        """Set trigger to falling edge."""
        self.write("EF")

    def enable_low_pass_filter(self, state):
        """Enable low pass filter."""
        if state:
            cmd = "FI"
        else:
            cmd = "FO"

        self.write(cmd)

    def set_measurement_time(self, meas_time):
        """Set measurement time."""
        assert meas_time in [
            0.3,
            1,
            10,
            100,
        ], "Invalid setting, the following times are supported: 0.3, 1, 10, 100 seconds"

        if meas_time == 0.3:
            val = 1
        elif meas_time == 1:
            val = 2
        elif meas_time == 10:
            val = 3
        else:
            val = 4

        self.write(f"M{val}")

    def every_measurement(self):
        """Get every measurement."""
        self.write("E?")

    def stop(self):
        """Stop measurement."""
        self.write("STOP")

    def identify(self):
        """Get instrument identification."""
        self.write("*IDN?")
        response = self.read().split(",")
        logger.debug(f"TF930.identify: response={response}")

        return {
            "name": response[0],
            "model": response[1],
            "version": response[3],
        }

    def model(self):
        """Get instrument model."""
        self.write("I?")
        return self.read()

    def reset(self):
        """Reset instrument."""
        self.write("*RST")

    def reset_measurement(self):
        """Reset measurement."""
        self.write("R")

    def status(self):
        """Get instrument status."""
        # TODO: Parse Bit Values, see manual
        self.write("S?")
        return self.read()

    # def set_ac_coupling(self):
