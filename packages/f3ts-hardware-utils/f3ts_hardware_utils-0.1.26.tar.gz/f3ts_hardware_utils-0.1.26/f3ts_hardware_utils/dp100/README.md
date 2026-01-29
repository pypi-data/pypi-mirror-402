# FixturFab Python wrapper for the Alientek DP100 power supply

Use this python wrapper for simple communication with the Alientek DP100 power supply within a pytest Test Plan.

## Dependencies

This python wrapper uses the [hid](https://pypi.org/project/hid/) and [crcmod](https://pypi.org/project/crcmod/) python libraries.  It has been tested on both Windows 11 and Ubuntu OS platforms.

Follow [this page](https://pypi.org/project/hid/) to install the necessary underlying HID libraries.

    * In Ubuntu, `sudo apt install libhidapi-hidraw0` works.  Then `sudo pip3 install crcmod hid`
    * In Win 11, the hidapi.dll file must be installed in the System32 folder.  Latest version of this .dll can be found at [hidapi](https://github.com/libusb/hidapi)

## Troubleshoot

1. Unable to open device issues

The DP100 must be connected to the host device using the USB-A to USB-A cable.  Make sure the power supply is in "USBD" 
(USB downstream) mode. Usually "USBD" mode is the default mode, you can double-tap ◀ to switch between USBD (downstream) and USBH (host).

Additionally, in Ubuntu:
    Use `lsusb` to check the usb bus number for "ALIENTEK ATK-MDP100", and use `ls -al /dev/bus/usb/xxx/` (xxx is the bus number for DP100) to check if the user has the permission to access the usb port. Note the HID device has root-only permission by default. To adjust USB permissions, copy the 99-atk-dp100.rules from this repo to the /etc/udev/rules.d/ folder on your computer, then run `sudo udevadm control --reload-rules` and re-plug the USB cable.

## Known Limitations
1. TBD...

## Reference

1. [pydp100](https://github.com/palzhj/pydp100) This python wrapper based on the pydp100 project script examples