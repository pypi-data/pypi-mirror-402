#!/usr/bin/env python3

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

reserve = gen24_registers.scaledMinRsvPct.get(fronius1)
print("Pre Res: %d" % reserve)

timeout = gen24_registers.InOutWRte_RvrtTms.get(fronius1)
print (" Timer: %d" % timeout)

# Reset timer
err = gen24_registers.InOutWRte_RvrtTms.set(fronius1, 0)
# This should be 'no limits' mode
err = gen24_registers.StorCtl_Mod.set(fronius1, 0)
# discharge at 100% allowed charge rate
err = gen24_registers.scaledOutWRte.set(fronius1, 100)
err = gen24_registers.scaledInWRte.set(fronius1, 100)
# charge to 7%
err = gen24_registers.scaledMinRsvPct.set(fronius1, 7)

discharge = gen24_registers.scaledOutWRte.get(fronius1)
print("Post DRate: %d%%" % discharge)

charge = gen24_registers.scaledInWRte.get(fronius1)
print("Post CRate: %d%%" % charge)

mode = gen24_registers.StorCtl_Mod.get(fronius1)
print("Post Mode: %d" % mode)

reserve = gen24_registers.scaledMinRsvPct.get(fronius1)
print("Post Res: %d" % reserve)

timeout = gen24_registers.InOutWRte_RvrtTms.get(fronius1)
print (" Timer: %d" % timeout)
