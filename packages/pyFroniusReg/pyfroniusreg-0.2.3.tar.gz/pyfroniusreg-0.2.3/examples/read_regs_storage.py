#!/usr/bin/env python3

from pyfroniusreg import gen24_primo_symo_inverter_register_map_int_sf_storage as gen24_registers
from pyfroniusreg.froniusreg import RegisterReadError

from pymodbus.client.tcp import ModbusTcpClient

fronius1 = ModbusTcpClient("172.19.107.211", port=502, timeout=10)
fronius1.connect()

print("   Manufacturer: %s" % gen24_registers.Mn.get(fronius1))
print("          Model: %s" % gen24_registers.Md.get(fronius1))
print("        Version: %s" % gen24_registers.Vr.get(fronius1))
print("            SOC: %s%%" % gen24_registers.scaledChaState.get(fronius1))
print("Max DCharg Rate: %d%%" % gen24_registers.scaledOutWRte.get(fronius1))
print("Max Charge Rate: %d%%" % gen24_registers.scaledInWRte.get(fronius1))
print("        Reserve: %d%%" % gen24_registers.scaledMinRsvPct.get(fronius1))
print("Max Charge rate: %dW" % gen24_registers.scaledMaxChaRte.get(fronius1))
print(" Current charge: %dW" % gen24_registers.scaledmodule_3_DCW.get(fronius1))
print(" Current dCharg:  %dW" % gen24_registers.scaledmodule_4_DCW.get(fronius1))
