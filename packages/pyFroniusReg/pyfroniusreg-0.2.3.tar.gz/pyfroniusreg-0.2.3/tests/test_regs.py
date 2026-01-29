#!/usr/bin/env python3
import unittest

from pyfroniusreg import gen24_primo_symo_inverter_register_map_int_sf_storage as gen24_registers
from pyfroniusreg import smart_meter_register_map_float as smart_meter

from pymodbus.client.tcp import ModbusTcpClient

fronius1 = ModbusTcpClient("172.19.107.211", port=502, timeout=10)
fronius1.connect()


class TestReadRegs(unittest.TestCase):
    def test_read_scaled(self):
        soc = gen24_registers.scaledChaState.get(fronius1)
        assert isinstance(soc, float)

    def test_read_direct(self):
        dr = gen24_registers.OutWRte.get(fronius1)
        assert isinstance(dr, int)

    def test_read_string16(self):
        Mn = gen24_registers.Mn.get(fronius1)
        assert Mn[0:7] == "Fronius"

    # def test_read_string8(self):
    #     # this isn't a good test, this value changes regularly
    #     Vr = gen24_registers.Vr.get(fronius1)
    #     assert Vr == "1.38.6-1"

    def test_read_model(self):
        # Also not a great test, but does test reading strings
        # and doesn't change as often
        Md = gen24_registers.Md.get(fronius1)
        assert Md == "Primo GEN24 5.0\x00"

    # def test_read_sn(self):
    # This doesn't seem to return anything useful
    # SN = gen24_registers.SN.get(fronius1)
    # assert SN == "12345567"

class testWriteRegs(unittest.TestCase):
    def test_write_direct(self):
        current = gen24_registers.OutWRte.get(fronius1)
        retval = gen24_registers.OutWRte.set(fronius1, current)
        assert retval is not None

    def test_write_scaled(self):
        current = gen24_registers.scaledInWRte.get(fronius1)
        retval = gen24_registers.scaledInWRte.set(fronius1, current)
        assert retval is not None

class testSmartMeter(unittest.TestCase):
    def test_freq_read(self):
        Hz = smart_meter.Hz.get(fronius1)
        assert isinstance(Hz, float)

    def test_import_read(self):
        wh_import = smart_meter.TotWhImp.get(fronius1)
        assert isinstance(wh_import, float)
    
if __name__ == "__main__":
    unittest.main()
    fronius1.close()
