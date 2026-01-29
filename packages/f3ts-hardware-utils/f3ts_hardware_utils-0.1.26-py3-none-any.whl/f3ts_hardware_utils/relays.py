"""
Relay Control.

This module provides utilities for working with USB Controlled Relay Modules
"""

import serial


class USBRelay(object):
    """SMAKN LCUS-1 USB Relay Module."""

    ON = [0xA0, 0x01, 0x01, 0xA2]
    OFF = [0xA0, 0x01, 0x00, 0xA1]

    def __init__(self, com_port):
        """Initialize connection to the Relay Modules COM port.

        :param com_port: COM port name (i.e. ttyUSB0
        :type com_port: str
        """
        self.ser = serial.Serial(port=com_port, baudrate=9800)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close relay hardware interfaces upon exit."""
        self.close()

    def close(self):
        """Close relay hardware interfaces."""
        self.ser.close()

    def set_state(self, state):
        """Set relay output state.

        Enable/disable the relay

        :param state: State to set relay to
        :type state: bool
        """
        if state:
            packet = self.ON
        else:
            packet = self.OFF

        self.ser.write(packet)

    def on(self):
        """Turn relay output on."""
        self.set_state(True)

    def off(self):
        """Turn relay output off."""
        self.set_state(False)
