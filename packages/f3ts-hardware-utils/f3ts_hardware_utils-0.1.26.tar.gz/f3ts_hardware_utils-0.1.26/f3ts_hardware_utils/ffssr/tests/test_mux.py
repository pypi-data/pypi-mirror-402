import time

from f3ts_hardware_utils.ffssr.serial_interface import FixturSSR, FixturSSRException

relay = FixturSSR()
relay.open()

# Information Stuff
print(f"    Manufacturer: {relay.manufacturer()}")
print(f"     Part Number: {relay.part_number()}")
print(f"Firmware Version: {relay.fw_version()}")
print(f" Card Identifier: {relay.card_identifier()}")

# ##################################################################
# Mux Tests
####################################################################

for channel in range(1, 16):
    relay.mux_chan_enable(channel)

relay.mux_off()
