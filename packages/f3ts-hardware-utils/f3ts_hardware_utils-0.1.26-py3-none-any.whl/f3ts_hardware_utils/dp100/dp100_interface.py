#!/usr/bin/env python
"""
FixturFab Alientek DP100 Power Supply Interface.

This module provides a clean, type-safe interface for controlling
the Alientek DP100 Power Supply via HID communication.
"""

import logging
import time
import platform
import atexit
from typing import List, Dict, TypedDict, Optional, Any, Union, Tuple
from contextlib import contextmanager

import hid
import crcmod

__author__ = "D. Wilkins (Optimized via Claude 3.7 Sonnet)"
__version__ = "0.2.0"
__email__ = "dave@fixturfab.com"

# Configure logger
logger = logging.getLogger(__name__)

# Constants for HID communication
HID_DELAY = 0.05          # Seconds
HID_BUFSIZE = 64          # Bytes
HID_TIMEOUT = 1.0         # Seconds for operations timeout

# Protocol constants
DR_H2D = 0xFB      # Direction flag (Host to Device)
DR_D2H = 0xFA      # Direction flag (Device to Host)
SET_MODIFY = 0x20
SET_ACT = 0x80

# Operation codes
OP_NONE = 0x00
OP_DEVICEINFO = 0x10
OP_SUPPLYGET = 0x30
OP_SUPPLYSET = 0x35
OP_SYSTEMINFO = 0x40
OP_SCANOUT = 0x50
OP_SERIALOUT = 0x55

# CRC16 generator function
crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)

# Platform detection
IS_WINDOWS = platform.system() == "Windows"

# Type definitions
class PowerStatus(TypedDict):
    """Power supply status information."""
    state: str      # 'On' or 'Off'
    vin: float      # Input voltage (V)
    vout: float     # Output voltage (V)
    iout: float     # Output current (A)
    temp: float     # Temperature (°C)

class PowerInfo(TypedDict):
    """Power supply device information."""
    dev_name: str   # Device Product Name
    hw_ver: str     # Hardware Version
    app_ver: str    # Application Version
    boot_ver: str   # Bootloader Version

class RawPowerStatus(TypedDict):
    """Raw power supply status information (internal use)."""
    vin: int
    vout: int
    iout: int
    vo_max: int
    temp: int
    mode: int

class RawDeviceInfo(TypedDict):
    """Raw device information (internal use)."""
    dev_type: str
    hw_ver: int
    app_ver: int
    boot_ver: int


class DP100Exception(Exception):
    """Custom exception class for Alientek DP100 Power Supply errors."""
    pass


class AlientekDP100:
    """
    FixturFab's Alientek DP100 HID Interface.
    
    This class provides methods to control the Alientek DP100 Power Supply
    via HID communication, allowing setting voltage/current, monitoring status,
    and retrieving device information.
    
    Attributes:
        vid (int): USB Vendor ID
        pid (int): USB Product ID
        serial_num (Optional[str]): Device serial number
        manufacturer (Optional[str]): Device manufacturer name
        product (Optional[str]): Device product name
    """

    def __init__(self, vid: int = 0x2e3c, pid: int = 0xaf01, serial_num: Optional[str] = None,
                 ovp: float = 30.5, ocp: float = 5.05):
        """
        Initialize the AlientekDP100 interface.
        
        Args:
            vid: USB Vendor ID (default: 0x2e3c for Alientek)
            pid: USB Product ID (default: 0xaf01 for DP100)
            serial_num: Optional serial number to specify a unique device
            ovp: Over-voltage protection setting in volts (default: 30.5V)
            ocp: Over-current protection setting in amps (default: 5.05A)
        """
        self.vid = vid
        self.pid = pid
        self.serial_num = serial_num
        self.manufacturer: Optional[str] = None
        self.product: Optional[str] = None
        self.hid: Optional[hid.Device] = None
        self.ovp = int(ovp * 1000)  # Convert to mV
        self.ocp = int(ocp * 1000)  # Convert to mA
        
    def __del__(self) -> None:
        """Ensure device is properly closed when object is destroyed."""
        self.close()
        
    def __enter__(self) -> 'AlientekDP100':
        """Context manager entry point."""
        self.open()
        return self
        
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit point."""
        self.close()

    # ##################################################################################
    # HID Discovery & Connection
    # ##################################################################################

    def open(self) -> None:
        """
        Open HID interface on Alientek DP100. 
        
        If no serial number is provided, checks for exactly one device.
        
        Raises:
            DP100Exception: If no device found, multiple devices found without serial number,
                           or if there's an IO error during connection.
        """
        try:
            # If already open, do nothing
            if self.hid is not None:
                return
                
            if self.serial_num:
                # Connect to specific device if serial number provided
                self.hid = hid.Device(vid=self.vid, pid=self.pid, serial=self.serial_num)
                self.manufacturer = 'ALIENTEK'
                self.product = 'ATK-MDP100'
            else:
                # Otherwise, make sure there's only one device available
                dp100_list = self.list_devices()
                
                for device in dp100_list:
                    logger.info(f"Found: {device['manufacturer']} {device['product']} "
                                f"(Serial Number = {device['serial_num']})")
                
                if not dp100_list:
                    raise DP100Exception("No Alientek DP100 devices found in system")
                    
                if len(dp100_list) > 1:
                    raise DP100Exception("Multiple DP100 devices found. Please specify "
                                        "serial number to connect to a specific device")
                
                # Connect to the single device found
                self.hid = hid.Device(vid=self.vid, pid=self.pid)
                self.manufacturer = dp100_list[0]['manufacturer']
                self.product = dp100_list[0]['product']
                self.serial_num = dp100_list[0]['serial_num']

            # Register safety shutdown handler
            atexit.register(self.power_off)

        except hid.HIDException as e:
            raise DP100Exception(f"HID error: {str(e)}")
        except Exception as e:
            raise DP100Exception(f"Error connecting to device: {str(e)}")

    def close(self) -> None:
        """
        Close the Alientek DP100 HID interface and turn off the power supply.
        
        This method is safe to call multiple times.
        """
        try:
            if self.hid is not None:
                self.power_off()
                self.hid.close()
                self.hid = None
                # Remove safety shutdown handler
                atexit.unregister(self.power_off)
        except Exception as e:
            logger.error(f"Error closing device: {str(e)}")

    def list_devices(self) -> List[Dict[str, str]]:
        """
        Return a list of Alientek DP100 devices enumerated in the system.
        
        Returns:
            List of dictionaries containing manufacturer, product, and serial number
            for each detected DP100 device.
            
        Raises:
            DP100Exception: If there's an error enumerating devices.
        """
        try:
            logger.info(f"Looking for HID devices with VID:PID = {self.vid:04X}:{self.pid:04X}")
            device_list = hid.enumerate(vid=self.vid, pid=self.pid)
            
            dp100_list = []
            for device in device_list:
                dp100_list.append({
                    "manufacturer": device['manufacturer_string'],
                    "product": device['product_string'],
                    "serial_num": device['serial_number']
                })
            return dp100_list
        except Exception as e:
            raise DP100Exception(f"Error listing devices: {str(e)}")

    # ##################################################################################
    # Low-level Communication
    # ##################################################################################

    def _gen_set_command(self, out_en: bool = False, vset: int = 0, iset: int = 0) -> bytes:
        """
        Generate DP100 output setting byte sequence.
        
        Args:
            out_en: Enable output (True/False)
            vset: Voltage setting in mV
            iset: Current setting in mA
            
        Returns:
            Byte sequence for setting command
        """
        output = 1 if out_en else 0
        return bytes([
            SET_MODIFY, 
            output, 
            vset & 0xFF, (vset >> 8) & 0xFF, 
            iset & 0xFF, (iset >> 8) & 0xFF,
            self.ovp & 0xFF, (self.ovp >> 8) & 0xFF, 
            self.ocp & 0xFF, (self.ocp >> 8) & 0xFF
        ])

    def _gen_frame(self, op_code: int, data: bytes = b'') -> bytes:
        """
        Generate DP100 HID communication frame with proper formatting and CRC.
        
        Args:
            op_code: Operation code
            data: Optional data bytes
            
        Returns:
            Complete frame with header, data, and CRC
        """
        # Add platform-specific header
        if IS_WINDOWS:
            # Windows requires a report ID as the first byte
            frame = bytes([0x00, DR_H2D, op_code & 0xFF, 0x0, len(data) & 0xFF]) + data
            crc = crc16(frame[1:])  # Skip report ID for CRC calculation
        else:
            # Other platforms don't use report ID
            frame = bytes([DR_H2D, op_code & 0xFF, 0x0, len(data) & 0xFF]) + data
            crc = crc16(frame)
            
        # Append CRC to frame
        return frame + bytes([crc & 0xFF, (crc >> 8) & 0xFF])

    def _send_receive(self, op_code: int, data: bytes = b'') -> bytes:
        """
        Send a command to the device and receive response.
        
        Args:
            op_code: Operation code
            data: Optional data bytes
            
        Returns:
            Raw response bytes
            
        Raises:
            DP100Exception: If device is not connected or communication fails
        """
        if self.hid is None:
            raise DP100Exception("Device not connected")
            
        try:
            frame = self._gen_frame(op_code, data)
            self.hid.write(frame)
            time.sleep(HID_DELAY)
            response = self.hid.read(HID_BUFSIZE, timeout=int(HID_TIMEOUT * 1000))
            
            if not response:
                raise DP100Exception("No response from device")
                
            return bytes(response)
        except hid.HIDException as e:
            raise DP100Exception(f"HID communication error: {str(e)}")

    def _verify_response(self, response: bytes, min_length: int = 4) -> Tuple[bytes, int]:
        """
        Verify that a response is valid and extract data portion.
        
        Args:
            response: Raw response bytes
            min_length: Minimum expected length for valid response
            
        Returns:
            Tuple of (data bytes, data length)
            
        Raises:
            DP100Exception: If response is invalid or has CRC error
        """
        if len(response) < min_length:
            raise DP100Exception(f"Response too short: {len(response)} bytes")
            
        if response[0] != DR_D2H:
            raise DP100Exception("Invalid response: not from device")
            
        data_len = response[3]
        expected_len = 4 + data_len + 2  # header + data + CRC
        
        if len(response) < expected_len:
            raise DP100Exception(f"Incomplete response: expected {expected_len}, got {len(response)}")
            
        # Verify CRC
        if crc16(response[0:expected_len]) != 0:
            raise DP100Exception("CRC error in response")
            
        # Return data portion and length
        return response[4:4+data_len], data_len

    # ##################################################################################
    # Device Command Implementation
    # ##################################################################################

    def _send_power_cmd(self, vout: float = 0, iout: float = 0, output: bool = False) -> None:
        """
        Send power command to the device and verify response.
        
        Args:
            vout: Output voltage in volts
            iout: Output current in amps
            output: True to enable output, False to disable
            
        Raises:
            DP100Exception: If voltage input is too low or communication fails
        """
        # Convert to millivolts/milliamps
        vset = int(vout * 1000)
        iset = int(iout * 1000)

        # Generate and send command
        command = self._gen_set_command(output, vset, iset)
        self._send_receive(OP_SUPPLYSET, command)
        
        # Allow supply to settle
        time.sleep(0.1)
        
        # Verify settings were applied
        if output:
            status = self._get_raw_power_status()
            vo_max = status['vo_max']
            
            if vo_max < vset:
                self.power_off()  # Safety: turn off if voltage can't be reached
                raise DP100Exception(
                    f"Input voltage ({status['vin']/1000:.3f}V) too low "
                    f"to set output to {vout:.3f}V"
                )

    def _get_raw_power_status(self) -> RawPowerStatus:
        """
        Get raw power supply status data.
        
        Returns:
            Dictionary with raw status values
            
        Raises:
            DP100Exception: If communication fails
        """
        response = self._send_receive(OP_SUPPLYGET)
        data, _ = self._verify_response(response)
        
        return {
            "vin": (data[1] << 8) | data[0],
            "vout": (data[3] << 8) | data[2],
            "iout": (data[5] << 8) | data[4],
            "vo_max": (data[7] << 8) | data[6],
            "temp": (data[9] << 8) | data[8],
            "mode": data[14]
        }

    def _get_raw_device_info(self) -> RawDeviceInfo:
        """
        Get raw device information.
        
        Returns:
            Dictionary with raw device information
            
        Raises:
            DP100Exception: If communication
        """
        response = self._send_receive(OP_DEVICEINFO)
        data, _ = self._verify_response(response)
        
        # Extract device name (null-terminated string)
        dev_name_bytes = data[0:15]
        null_pos = dev_name_bytes.find(0)
        if null_pos != -1:
            dev_name = dev_name_bytes[:null_pos].decode("utf-8")
        else:
            dev_name = dev_name_bytes.decode("utf-8")
        
        return {
            "dev_type": dev_name,
            "hw_ver": (data[17] << 8) | data[16],
            "app_ver": (data[19] << 8) | data[18],
            "boot_ver": (data[21] << 8) | data[20]
        }

    # ##################################################################################
    # Public Methods
    # ##################################################################################

    def power_on(self, vout: float = 0, iout: float = 0) -> None:
        """
        Turn on the DP100 power supply with specified voltage and current.
        
        Args:
            vout: Output voltage in volts
            iout: Output current in amps
            
        Raises:
            DP100Exception: If device is not connected, input voltage is too low,
                           or communication fails
        """
        if self.hid is None:
            self.open()
            
        # Input validation
        if vout < 0 or vout > 30:
            raise DP100Exception(f"Invalid voltage: {vout}V (must be 0-30V)")
            
        if iout < 0 or iout > 5:
            raise DP100Exception(f"Invalid current: {iout}A (must be 0-5A)")
            
        if vout * iout > 100:
            raise DP100Exception(f"Invalid wattage: {vout*iout}W (must be < 100W)")
        
        self._send_power_cmd(vout, iout, True)
        logger.info(f"Power supply turned ON: {vout:.3f}V, {iout:.3f}A")

    def power_off(self) -> None:
        """
        Turn off the DP100 power supply.

        This method is safe to call even if the device is not connected or
        if the USB handle has been invalidated (e.g., during interpreter shutdown).
        """
        if self.hid is not None:
            try:
                self._send_power_cmd(0, 0, False)
                logger.info("Power supply turned OFF")
            except OSError as e:
                # Handle case where USB handle is already invalid (common on Windows
                # during interpreter shutdown when atexit handler runs after the
                # system has already released the USB handle)
                if IS_WINDOWS and e.winerror == 6:  # ERROR_INVALID_HANDLE
                    logger.debug("USB handle already closed during shutdown")
                else:
                    logger.error(f"Error turning off power: {str(e)}")
            except Exception as e:
                logger.error(f"Error turning off power: {str(e)}")
    
    def power_status(self) -> PowerStatus:
        """
        Get the current power supply status.
        
        Returns:
            PowerStatus dictionary with state, voltage, current, and temperature
            
        Raises:
            DP100Exception: If device is not connected or communication fails
        """
        if self.hid is None:
            self.open()
            
        status = self._get_raw_power_status()
        
        # Convert raw values to user-friendly format
        vin = status['vin'] / 1000
        vout = status['vout'] / 1000
        iout = status['iout'] / 1000
        temp = status['temp'] / 10
        state = 'Off' if status['mode'] else 'On'
        
        logger.info(f'Supply {state} - Vin: {vin:.3f}V, Vout: {vout:.3f}V, '
                   f'Iout: {iout:.3f}A, temperature: {temp:.1f}°C')
        
        return {
            "state": state,
            "vin": vin,
            "vout": vout,
            "iout": iout,
            "temp": temp,
        }

    def device_info(self) -> PowerInfo:
        """
        Get device information.
        
        Returns:
            PowerInfo dictionary with device name and version information
            
        Raises:
            DP100Exception: If device is not connected or communication fails
        """
        if self.hid is None:
            self.open()
            
        info = self._get_raw_device_info()
        
        # Convert raw values to user-friendly format
        dev_name = info['dev_type']
        hw_ver = info['hw_ver'] / 10
        app_ver = info['app_ver'] / 10
        boot_ver = info['boot_ver'] / 10
        
        logger.info(f'{dev_name} hardware={hw_ver:.1f} app={app_ver:.1f} bootloader={boot_ver:.1f}')
        
        return {
            "dev_name": dev_name,
            "hw_ver": f"{hw_ver:.1f}",
            "app_ver": f"{app_ver:.1f}",
            "boot_ver": f"{boot_ver:.1f}",
        }

    def set_voltage(self, vout: float) -> None:
        """
        Set voltage while maintaining current setting.
        
        Args:
            vout: Output voltage in volts
            
        Raises:
            DP100Exception: If device is not connected or communication fails
        """
        if self.hid is None:
            self.open()
            
        # Get current status
        status = self._get_raw_power_status()
        current_iout = status['iout'] / 1000
        is_on = status['mode'] == 0  # 0 means ON
        
        # Update voltage while maintaining current and power state
        self._send_power_cmd(vout, current_iout, is_on)
        logger.info(f"Voltage set to {vout:.3f}V")

    def set_current(self, iout: float) -> None:
        """
        Set current while maintaining voltage setting.
        
        Args:
            iout: Output current in amps
            
        Raises:
            DP100Exception: If device is not connected or communication fails
        """
        if self.hid is None:
            self.open()
            
        # Get current status
        status = self._get_raw_power_status()
        current_vout = status['vout'] / 1000
        is_on = status['mode'] == 0  # 0 means ON
        
        # Update current while maintaining voltage and power state
        self._send_power_cmd(current_vout, iout, is_on)
        logger.info(f"Current set to {iout:.3f}A")

    def set_ovp(self, ovp: float) -> None:
        """
        Set over-voltage protection value.
        
        Args:
            ovp: Over-voltage protection threshold in volts
            
        Raises:
            DP100Exception: If value is out of range
        """
        if ovp < 0 or ovp > 33:
            raise DP100Exception(f"Invalid OVP value: {ovp}V (must be 0-33V)")
            
        self.ovp = int(ovp * 1000)
        logger.info(f"OVP set to {ovp:.3f}V")

    def set_ocp(self, ocp: float) -> None:
        """
        Set over-current protection value.
        
        Args:
            ocp: Over-current protection threshold in amps
            
        Raises:
            DP100Exception: If value is out of range
        """
        if ocp < 0 or ocp > 5.5:
            raise DP100Exception(f"Invalid OCP value: {ocp}A (must be 0-5.5A)")
            
        self.ocp = int(ocp * 1000)
        logger.info(f"OCP set to {ocp:.3f}A")

    @contextmanager
    def temporarily_powered(self, vout: float = 0, iout: float = 0):
        """
        Context manager to temporarily power on the device.
        
        Args:
            vout: Output voltage in volts
            iout: Output current in amps
            
        Example:
            with dp100.temporarily_powered(5.0, 1.0):
                # Do something with power on
                time.sleep(2)
            # Power is automatically turned off when exiting the block
        """
        try:
            self.power_on(vout, iout)
            yield
        finally:
            self.power_off()


# Helper functions for users of the library
def discover_dp100_devices() -> List[Dict[str, str]]:
    """
    Discover all DP100 devices connected to the system.
    
    Returns:
        List of dictionaries with device information
    """
    dp100 = AlientekDP100()
    return dp100.list_devices()


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure logging for the DP100 interface.
    
    Args:
        level: Logging level (use logging.DEBUG, logging.INFO, etc.)
    """
    logger.setLevel(level)
    
    # Add console handler if not already present
    if not logger.handlers:
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)


# Example usage
if __name__ == "__main__":
    # Enable logging
    configure_logging(logging.INFO)
    
    # Example 1: Basic usage
    print("Example 1: Basic usage")
    dp100 = AlientekDP100()
    
    try:
        dp100.open()
        print("Device info:", dp100.device_info())
        
        # Power on with 5V, 0.5A
        dp100.power_on(5.0, 0.010)
        
        # Wait a bit
        time.sleep(1)
        
        # Get status
        status = dp100.power_status()
        print(f"Status: {status}")
        
        # Change voltage
        dp100.set_voltage(3.3)
        time.sleep(1)
        
        # Power off
        dp100.power_off()
    finally:
        dp100.close()
    
    # Example 2: Using context manager
    print("\nExample 2: Context manager")
    with AlientekDP100() as dp100:
        print("Device info:", dp100.device_info())
        
        # Use temporary power
        with dp100.temporarily_powered(5.0, 0.010):
            print("Power temporarily on")
            status = dp100.power_status()
            print(f"Status: {status}")
            time.sleep(1)
            
        print("Power should be off now")
        status = dp100.power_status()
        print(f"Status: {status}")
