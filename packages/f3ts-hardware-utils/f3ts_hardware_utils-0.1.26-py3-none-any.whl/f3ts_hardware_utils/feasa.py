"""Feasa LED Analyzer Python Interface."""
import serial


class Feasa(object):
    """Feasa LED Analyzer."""

    def __init__(self, port):
        """Initialize connection to the Feasa LED Analyzer."""
        self.ser = serial.Serial(baudrate=57600, port=port)

    def capture(self, intensity_range=""):
        """Capture the RGBI values for the given channel."""
        self.ser.write(f"capture{intensity_range}\r\n".encode("utf-8"))
        response = self.ser.readline().decode("utf-8")
        assert "OK" in response

    def capture_pwm(self, intensity_range="", averaging_factor=""):
        """Capture the RGBI values for the given channel."""
        self.ser.write(f"capture{intensity_range}pwm{averaging_factor}\r\n")
        response = self.ser.readline().decode("utf-8")
        assert "OK" in response

    def get_rgbi(self, channel):
        """Return the RGBI values for the given channel."""
        self.ser.write(f"getrgbi{channel:02}\r\n".encode("utf-8"))
        response = self.ser.readline().decode("utf-8").split(" ")
        return {
            "r": int(response[0]),
            "g": int(response[1]),
            "b": int(response[2]),
            "i": int(response[3]),
        }

    def close(self):
        """Close connection to the Feasa LED Analyzer."""
        self.ser.close()
