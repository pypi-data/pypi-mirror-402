import statistics
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

# Print ADC & Voltage readings statistics for both positive and
# negative terminals on a particular Mux channel.  Used for ADC
# characterization of ADC stability & noise.

channel = 1
terminal = "+"
iterations = 100
average_over = 4

adc = []
volts = []

relay.mux_chan_enable(channel)

for i in range(iterations):
    adc.append(relay.mux_adc(terminal=terminal, average=average_over))
    volts.append(relay.mux_voltage(terminal=terminal, average=average_over))
    # time.sleep(0.01)

adc_mean = statistics.mean(adc)
adc_median = statistics.median(adc)
adc_std_dev = statistics.stdev(adc)
adc_variance = statistics.variance(adc)
adc_min = min(adc)
adc_max = max(adc)
adc_span = 100 * (adc_max - adc_min) / adc_mean / 2

volts_mean = statistics.mean(volts)
volts_median = statistics.median(volts)
volts_std_dev = statistics.stdev(volts)
volts_variance = statistics.variance(volts)
volts_min = min(volts)
volts_max = max(volts)
volts_span = 100 * (volts_max - volts_min) / volts_mean / 2

print(f"ADC Mean:       {round(adc_mean)} \tVolts Mean:     {volts_mean:.3f}")
print(f"ADC Median:     {round(adc_median)} \tVolts Median:   {volts_median:.3f}")
print(f"ADC StdDev:     {round(adc_std_dev)} \tVolts StdDev:   {volts_std_dev:.3f}")
print(f"ADC Variance:   {round(adc_variance)} \tVolts Variance: {volts_variance:.3f}")
print(f"ADC Span(+/-):  {adc_span:0.2f}% \tVolts Span(+/-):{volts_span:0.2f}%")

relay.mux_off()
