import time
from dp100_interface import AlientekDP100, DP100Exception

try:
    dp100 = AlientekDP100()                            # Fully automatic (works if a single DP100 is in system)
    devices = dp100.list_devices()
    print ('Found these DP-100 devices in system:')
    for device in devices:
        print (device)
    #quit()


    dp100.open()
    print("Device info:", dp100.device_info())
    
    # Power on Supply#1 with 5V, 0.01A
    dp100.power_on(5.0, 0.010)
    
    # Wait a bit
    time.sleep(5)           # Enough time that supplies can be visually inspected

    dp100.close()         # Should turn off both supplies

except DP100Exception as e:
    print(f"An Alientek DP100 error occured: {e}")
except Exception as e:
    print(f"An unexpected error occured: {e}")