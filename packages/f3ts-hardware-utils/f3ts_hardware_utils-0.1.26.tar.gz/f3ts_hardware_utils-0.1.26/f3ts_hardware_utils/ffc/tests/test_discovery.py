from f3ts_hardware_utils.ffc.serial_interface import FixturCNTL, FixturCNTLException

""" Various example of binding options
"""
fixture = FixturCNTL()  # Fully automatic
# fixture = FixtureController(port="COM4")          # Specific Serial Port (Can be Windows || Linux scheme)
# fixture = FixtureController(port="/dev/ttyACM0")  # Specific Serial Port (Can be Windows || Linux scheme)

try:
    fixture.open()
    print(f"Successfully attached @ {fixture.port}: {fixture.who()}")
except FixturCNTLException as e:
    print(f"A FixturCNTL error occured: {e}")
except Exception as e:
    print(f"An unexpected error occured: {e}")
