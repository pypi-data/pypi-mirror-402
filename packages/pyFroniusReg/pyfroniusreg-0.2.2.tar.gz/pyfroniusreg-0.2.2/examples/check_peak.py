#!/usr/bin/env python3

import statistics

from pyfroniusreg import gen24_primo_symo_inverter_register_map_int_sf_storage as gen24_registers
from pyfroniusreg.froniusreg import RegisterReadError

from datetime import datetime

from pymodbus.client.tcp import ModbusTcpClient

# ModBUS connection to the inverter
fronius1 = ModbusTcpClient("172.19.107.211", port=502, timeout=10)
fronius1.connect()

# Info Registers
soc_percent = gen24_registers.scaledChaState.get(fronius1)
total_wh = gen24_registers.scaledWHRtg.get(fronius1)

# Charge Registers
discharge = gen24_registers.scaledOutWRte.get(fronius1)
charge = gen24_registers.scaledInWRte.get(fronius1)
mode = gen24_registers.StorCtl_Mod.get(fronius1)
timer = gen24_registers.InOutWRte_RvrtTms.get(fronius1)

current_time = datetime.now()

charge_data = []
discharge_data = []

print("Gathering 5 second average of battery power")
while( (datetime.now() - current_time).seconds < 5):
    charge_data.append(gen24_registers.scaledmodule_3_DCW.get(fronius1))
    discharge_data.append(gen24_registers.scaledmodule_4_DCW.get(fronius1))

avg_charge = statistics.mean(charge_data)
avg_discharge = statistics.mean(discharge_data)
print("   Charge: %.2f" % avg_charge)
print("DisCharge: %.2f" % avg_discharge)
print("      SoC: %.2f" % soc_percent)
print("Total  WH: %.2f" % total_wh)
print("    Timer: %d" % timer)

wh_remain = (soc_percent / 100.0) * total_wh
h_estim = wh_remain - (avg_discharge - avg_charge)
h_estpct = (h_estim / total_wh) * 100
two_h_estpct = h_estpct * 2.0

print("WH remain: %.2f" % wh_remain)
print("1h est WH: %.2f" % h_estim)
print("2hr est %%: %.2f" % two_h_estpct)


time_check = (current_time.hour == 5 or current_time.hour == 14)
estimate_check = (two_h_estpct < 22.0)

if (time_check and estimate_check):
    print("Full BEEEEEAAAAANS!")
    # Set settings timer to 115 minutes
    err = gen24_registers.InOutWRte_RvrtTms.set(fronius1, 6900)
    # This should be 'limit discharge' mode
    print("Setting control mode to limit discharge")
    err = gen24_registers.StorCtl_Mod.set(fronius1, 2)
    # Charge battery at a rate from -2% discharge to 100% charge
    # as a percentage of the MaxChaRte, which in our case is 25600W
    print("Setting discharge rate to -10%")
    err = gen24_registers.scaledOutWRte.set(fronius1, int(-20))
    print("Setting charge rate to 100%")
    err = gen24_registers.scaledInWRte.set(fronius1, int(100))

    
else:
    print("Nothing doing")
