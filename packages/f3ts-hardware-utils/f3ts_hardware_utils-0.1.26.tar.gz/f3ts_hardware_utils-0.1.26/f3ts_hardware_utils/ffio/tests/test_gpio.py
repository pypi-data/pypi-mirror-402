import time

from f3ts_hardware_utils.ffio.serial_interface import FixturIO

gpio = FixturIO()
gpio.open()
gpio.reset()  # Ensure FixturIO in default rebooted state
time.sleep(1)  # Let device re-ennumerate
gpio.open()  # Open in fresh state

# Information Stuff
print(f"    Manufacturer: {gpio.manufacturer()}")
print(f"     Part Number: {gpio.part_number()}")
print(f"Firmware Version: {gpio.fw_version()}")
print(f" Card Identifier: {gpio.card_identifier()}")

# ##################################################################
# GPIO Tests
####################################################################

# Digital IO Stuff
for i in range(100):
    for pin in range(37):
        gpio.set_gpio_mode(gpio=pin, mode="out")

    for pin in range(37):
        gpio.set_gpio_state(gpio=pin, state=1)
        time.sleep(0.005)
        gpio.set_gpio_state(gpio=pin, state=0)
