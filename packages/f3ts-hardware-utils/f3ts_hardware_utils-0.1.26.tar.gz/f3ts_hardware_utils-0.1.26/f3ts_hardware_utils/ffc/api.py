"""Fixture Controller FastAPI Router."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder

from .serial_interface import FixturCNTL

router = APIRouter()

router.PORT = None
router.BAUD = 57600
router.TIMEOUT = 1


def get_fixture_controller():
    """Get fixture controller device."""
    fixture_controller = None
    try:
        fixture_controller = FixturCNTL(
            port=router.PORT, baud=router.BAUD, timeout=router.TIMEOUT
        )
        fixture_controller.open()
    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Unable to connect to serial device"
            + jsonable_encoder(fixture_controller),
        )

    try:
        yield fixture_controller
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected Error: {e}",
        )
    finally:
        if fixture_controller:
            fixture_controller.close()


@router.get("/serial/config", status_code=200)
def get_serial_config(
    fixture_controller: FixturCNTL = Depends(get_fixture_controller),
):
    """Get fixture controller serial interface configuration."""
    return fixture_controller


@router.post("/serial/config", status_code=200)
def set_serial_config(port: str = None, baud: int = 56700, timeout: float = 1):
    """
    Set fixture controller serial interface configuration.

    Set port to None for autodiscovery.
    """
    router.PORT = port
    router.BAUD = baud
    router.TIMEOUT = timeout

    try:
        fixture_controller = FixturCNTL(
            port=router.PORT, baud=router.BAUD, timeout=router.TIMEOUT
        )
        fixture_controller.open()
        fixture_controller.close()
        return fixture_controller
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to connect to serial device \
            {jsonable_encoder(fixture_controller)}",
        )


@router.get("/get_close_state", status_code=200)
def get_close_state(
    fixture_controller: FixturCNTL = Depends(get_fixture_controller),
) -> bool:
    """Get close state of fixture."""
    output = fixture_controller.get_fixture_closed()
    return output


@router.get("/firmware_version", status_code=200)
def firmware_version(
    fixture_controller: FixturCNTL = Depends(get_fixture_controller),
) -> str:
    """Get firmware version."""
    output = fixture_controller.firmware_version()
    return output


@router.post("/usb/all", status_code=200)
def usb_port_enable_all(
    fixture_controller: FixturCNTL = Depends(get_fixture_controller),
    enable: bool = True,
) -> str:
    """Enable all USB ports."""
    output = fixture_controller.usb_port_enable_all(state=enable)
    return output


@router.post("/usb", status_code=200)
def usb_port_enable(
    fixture_controller: FixturCNTL = Depends(get_fixture_controller),
    enable: bool = True,
    port: int = 1,
) -> str:
    """Get close state of fixture."""
    output = fixture_controller.usb_port_enable(state=enable, port=port)
    return output


@router.get("/cycles", status_code=200)
def get_cycles(
    fixture_controller: FixturCNTL = Depends(get_fixture_controller),
    eeprom: int = 1,
) -> int:
    """Get cycle counter from desired eeprom."""
    output = fixture_controller.get_cycles(eeprom=eeprom)
    return output


@router.post("/cycles", status_code=200)
def zero_cycles(
    fixture_controller: FixturCNTL = Depends(get_fixture_controller),
    eeprom: int = 1,
) -> int:
    """Zero out cycle counter from desired eeprom."""
    fixture_controller.zero_cycles(eeprom=eeprom)
    output = fixture_controller.get_cycles(eeprom=eeprom)
    return output


@router.get("/i2c_eeprom", status_code=200)
def get_i2c_eeprom_devices(
    fixture_controller: FixturCNTL = Depends(get_fixture_controller),
) -> list:
    """List connected i2c eeprom devices."""
    output = fixture_controller.get_i2c_eeprom_devices()
    return output


@router.post("/gpio/mode", status_code=200)
def set_gpio_mode(
    *,
    fixture_controller: FixturCNTL = Depends(get_fixture_controller),
    pin: int,
    mode: str,
):
    """Set gpio pin to desired mode ('in' or 'out')."""
    fixture_controller.set_gpio_mode(gpio=pin, mode=mode)
    return mode


@router.get("/gpio/state", status_code=200)
def get_gpio_state(
    *,
    fixture_controller: FixturCNTL = Depends(get_fixture_controller),
    pin: int,
) -> bool:
    """Get gpio pin's current state ."""
    output = fixture_controller.get_gpio_state(gpio=pin)
    return output


@router.post("/gpio/state", status_code=200)
def set_gpio_state(
    *,
    fixture_controller: FixturCNTL = Depends(get_fixture_controller),
    pin: int,
    state: bool,
) -> bool:
    """Set gpio pin to desired state."""
    fixture_controller.set_gpio_state(gpio=pin, state=state)
    output = fixture_controller.get_gpio_state(gpio=pin)
    return output


@router.post("/gpio/state/all", status_code=200)
def set_gpio_state_all(
    *,
    fixture_controller: FixturCNTL = Depends(get_fixture_controller),
    state: bool,
) -> bool:
    """Set all gpio pins to desired state."""
    fixture_controller.set_gpio_state_all(state=state)
    return state


@router.get("/aio/voltage", status_code=200)
def get_analog_voltage(
    *,
    fixture_controller: FixturCNTL = Depends(get_fixture_controller),
    pin: int,
) -> float:
    """Get ADC pin's corresponding voltage."""
    output = fixture_controller.get_analog_state(aio=pin)
    return output
