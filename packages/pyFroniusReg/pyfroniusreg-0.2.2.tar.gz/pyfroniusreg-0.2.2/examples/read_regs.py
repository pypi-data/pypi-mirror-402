#!/usr/bin/env python3

from pyfroniusreg import gen24_primo_symo_inverter_register_map_float as gen24_registers
from pyfroniusreg.froniusreg import RegisterReadError

from pymodbus.client.tcp import ModbusTcpClient

fronius1 = ModbusTcpClient("172.19.107.249", port=502, timeout=10)
fronius1.connect()

print("   Manufacturer: %s" % gen24_registers.Mn.get(fronius1))
print("          Model: %s" % gen24_registers.Md.get(fronius1))
print("        Version: %s" % gen24_registers.Vr.get(fronius1))
print("       AC Power: %s" % gen24_registers.W.get(fronius1))
print("       DC Power: %s" % gen24_registers.DCW.get(fronius1))

