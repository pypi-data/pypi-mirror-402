"""PYOCD Programming Utilities."""

import logging

from pyocd.core.exceptions import TransferError
from pyocd.core.helpers import ConnectHelper
from pyocd.flash.file_programmer import FileProgrammer

logging.basicConfig(level=logging.DEBUG)


def flash_mcu(firmware_file: str, target_type: str) -> bool:
    """
    Flash a HEX file to a Arm Cortex-M CPU.

    Flash a HEX file to a Arm Cortex-M CPU using a CMSIS-DAP compatible
    programmer. The target must be supported by pyocd, if support for the
    target is not built in, a CMSIS pack can be installed to add support
    for the MCU. See here:
    http://www.keil.com/pack/doc/CMSIS/Pack/html/index.html

    :param firmware_file: Filename and directory of rvc_firmware file
    :type firmware_file: str
    :param target_type: Target part number string
    :type target_type: str
    :return: True if flashing was successful, False if not
    """
    try:
        session = ConnectHelper.session_with_chosen_probe(target_override=target_type)
        if session is None:
            return False

        with session:
            target = session.board.target

            # Load rvc_firmware into device.
            programmer = FileProgrammer(session)
            programmer.program(firmware_file)

            # Reset, run
            target.reset_and_halt()
            target.resume()

        return True

    except TransferError:
        return False
