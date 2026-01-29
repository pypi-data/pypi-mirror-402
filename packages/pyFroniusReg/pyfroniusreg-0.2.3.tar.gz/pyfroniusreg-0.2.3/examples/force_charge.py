#!/usr/bin/env python3

#from pyfroniusreg import gen24_registers
from pyfroniusreg import gen24_primo_symo_inverter_register_map_int_sf_storage as gen24_registers


from pymodbus.client.tcp import ModbusTcpClient

fronius1 = ModbusTcpClient("172.19.107.211", port=502, timeout=10)
fronius1.connect()

soc = gen24_registers.scaledChaState.get(fronius1)
print(" SOC: %s%%" % soc)

discharge = gen24_registers.scaledOutWRte.get(fronius1)
print("Pre DRate: %d%%" % discharge)

charge = gen24_registers.scaledInWRte.get(fronius1)
print("Pre CRate: %d%%" % charge)

mode = gen24_registers.StorCtl_Mod.get(fronius1)
print("Pre Mode: %d" % mode)

timeout = gen24_registers.InOutWRte_RvrtTms.get(fronius1)
print ("Timer: %d" % timeout)

# Set timer for 55 minutes
err = gen24_registers.InOutWRte_RvrtTms.set(fronius1, 3300)

# This should be 'limit discharge' mode
print("Setting control mode to limit discharge")
err = gen24_registers.StorCtl_Mod.set(fronius1, 2)

# Charge battery at a rate from -2% discharge to 100% charge
# as a percentage of the MaxChaRte, which in our case is 25600W
print("Setting discharge rate to -25%")
err = gen24_registers.scaledOutWRte.set(fronius1, int(-25))
print("Setting charge rate to 100%")
err = gen24_registers.scaledInWRte.set(fronius1, int(100))

discharge = gen24_registers.scaledOutWRte.get(fronius1)
print("Post DRate: %d%%" % discharge)

charge = gen24_registers.scaledInWRte.get(fronius1)
print("Post CRate: %d%%" % charge)

mode = gen24_registers.StorCtl_Mod.get(fronius1)
print("Post Mode: %d" % mode)
