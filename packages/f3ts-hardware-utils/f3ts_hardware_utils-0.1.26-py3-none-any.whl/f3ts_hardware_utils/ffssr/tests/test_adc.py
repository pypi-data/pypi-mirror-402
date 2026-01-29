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
# Mux ADC Tests (Jumpers must be set to ADC Mode)
####################################################################

# Print streaming ADC & Voltage readings for both positive and
# negative terminals on a particular channel.  Used for ADC
# characterization over ADC range.

channel = 1
iterations = 25

relay.mux_chan_enable(channel)

for i in range(iterations):
    adc_plus = relay.mux_adc(terminal="+", average=4)
    volts_plus = relay.mux_voltage(terminal="+", average=4)
    adc_minus = relay.mux_adc(terminal="-", average=4)
    volts_minus = relay.mux_voltage(terminal="-", average=4)

    print(
        f"Mux Chan {channel} (+)Term: {adc_plus} / {volts_plus:.3f}V (-)Term: {adc_minus} / {volts_minus:.3f}V"
    )

    time.sleep(0.1)

relay.mux_off()
