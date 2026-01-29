#!/usr/bin/env python3
import unittest

from pyfroniusreg import froniusreg


class TestDataTypes(unittest.TestCase):
    def test_int16(self):
        int16_buffer = froniusreg.int16.encode_to_buffer(1024)
        assert int16_buffer == [b"\x04\x00"]

    def test_int16_decode(self):
        int16_register = [0x0, 0x1, 0x0, 0x0, 0x0, 0x5, 0x1, 0x3, 0x2, 0x0, 0x0]
        output = froniusreg.int16.decode_from_register(int16_register)
        assert output == 0

    def test_string16(self):
        string_buffer = froniusreg.string16.encode_to_buffer("Fronius")
        assert string_buffer == [b"Fr", b"on", b"iu", b"s\x00"]

    def test_string_16_decode(self):
        int_register = [18034, 28526, 26997, 29440, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        output = froniusreg.string16.decode_from_register(int_register)
        expectation = "Fronius" + 9 * '\x00'
        assert output == expectation

if __name__ == "__main__":
    unittest.main()
