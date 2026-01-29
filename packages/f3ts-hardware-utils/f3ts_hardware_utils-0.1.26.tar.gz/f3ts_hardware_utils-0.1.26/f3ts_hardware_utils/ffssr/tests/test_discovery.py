from f3ts_hardware_utils.ffssr.serial_interface import FixturSSR, FixturSSRException

""" Various example of binding options
"""
relay = FixturSSR()  # Fully automatic (works if a single card is in system)
# relay = FixturSSR(card_id=0)                 # Specific Card Identifier (most robust, can have several cards in system)
# relay = FixturSSR(port="COM13")              # Specific Serial Port (Can be Windows || Linux scheme)
# relay = FixturSSR(port="/dev/ttyACM0")       # Specific Serial Port (Can be Windows || Linux scheme)
# relay = FixturSSR(port="COM5", card_id=0)    # Specific Port + Card Identifier (for completeness, not that helpful)
# relay = FixturSSR(port="/dev/ttyACM0", card_id=0)    # Specific Port + Card Identifier (for completeness, not that helpful)

try:
    relay.open()
    print(f"Successfully attached @ {relay.port}: {relay.who()}")
except FixturSSRException as e:
    print(f"A FixturSSR error occured: {e}")
except Exception as e:
    print(f"An unexpected error occured: {e}")
