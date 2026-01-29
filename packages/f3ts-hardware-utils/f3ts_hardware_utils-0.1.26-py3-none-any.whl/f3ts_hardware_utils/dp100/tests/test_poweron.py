import time
#from hid_interface import AlientekDP100, DP100Exception
from dp100_interface import AlientekDP100, DP100Exception

dp100 = AlientekDP100()                          # Fully automatic (works if a single DP100 is in system)
#dp100 = AlientekDP100(serial_num='223AF55DC000') # Specific serial number to attach to

try:
    dp100.open()
    print(f"Connected: {dp100.manufacturer} {dp100.product} (Serial Number = {dp100.serial_num})")

    dp100.power_on(vout = 5.0, iout = 0.010)
    for i in range (3):
        status = dp100.power_status()
        vin    = status['vin']
        vout   = status['vout']
        iout   = status['iout']
        temp   = status['temp']
        state  = status['state']
        print('Supply %s - Vin: %.3fV, Vout: %.3fV, Iout: %.3fA, temperature: %.1f degC'%(state, vin, vout, iout, temp))
        time.sleep(1)

    dp100.power_off()
    status = dp100.power_status()
    vin    = status['vin']
    vout   = status['vout']
    iout   = status['iout']
    temp   = status['temp']
    state  = status['state']
    print('Supply %s - Vin: %.3fV, Vout: %.3fV, Iout: %.3fA, temperature: %.1f degC'%(state, vin, vout, iout, temp))
    time.sleep(1)

    # Test closing (should power off supply), comment out close() to check supply is turned off when script terminates
    dp100.power_on(5.0, 0.010)
    time.sleep(1)
    #dp100.close()

except DP100Exception as e:
    print(f"An Alientek DP100 error occured: {e}")
except Exception as e:
    print(f"An unexpected error occured: {e}")