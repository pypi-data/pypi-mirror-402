from f3ts_hardware_utils.ffio.serial_interface import FixturIO, FixturIOException

gpio = FixturIO()  # Fully automatic (works if a single card is in system)
# gpio = FixturIO(card_id=0)                 # Specific Card Identifier (most robust, can have several cards in system)
# gpio = FixturIO(port="COM13")              # Specific Serial Port (Can be Windows || Linux scheme)
# gpio = FixturIO(port="/dev/ttyACM0")       # Specific Serial Port (Can be Windows || Linux scheme)
# gpio = FixturIO(port="COM3", card_id=1)    # Specific Port + Card Identifier (for completeness, not that helpful)
# gpio = FixturIO(port="/dev/ttyACM0", card_id=0)    # Specific Port + Card Identifier (for completeness, not that helpful)

# print(gpio.list_ports())                    # See what FixturIO ports are ennumerated

try:
    gpio.open()
    print(f"Successfully attached @ {gpio.port}: {gpio.who()}")
except FixturIOException as e:
    print(f"A FixturIO error occured: {e}")
except Exception as e:
    print(f"An unexpected error occured: {e}")
