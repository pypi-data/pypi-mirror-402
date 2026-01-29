# Python Fronius Registers
#
# Copyright 2024, Paul Warren <pwarren@pwarren.id.au>
# Licensed under AGPLv3, See LICENSE.md for terms

from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
from pymodbus.client.base import ModbusBaseClient


class DataType:
    def __init__(self, width, decode, add):
        width: int

        self._width = width
        self._decode = decode
        self._add = add

    @property
    def width(self):
        return self._width

    def decode_from_register(self, registers):
        decoder = BinaryPayloadDecoder.fromRegisters(
            registers, byteorder=Endian.BIG, wordorder=Endian.BIG
        )
        return self._decode(decoder)

    def encode_to_buffer(self, value):
        encoder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.BIG)
        self._add(encoder, value)
        return encoder.build()


# helper functions for DataType constructors
def decode_string4(decoder) -> str:
    try:
        return str(decoder.decode_string(4).decode("utf-8"))
    except UnicodeDecodeError:
        return decoder.decode_string(4)


def decode_string8(decoder) -> str:
    try:
        return str(decoder.decode_string(8).decode("utf-8"))
    except UnicodeDecodeError:
        return decoder.decode_string(8)


def decode_string16(decoder) -> str:
    try:
        return str(decoder.decode_string(16).decode("utf-8"))
    except UnicodeDecodeError:
        return decoder.decode_string(16)


def encode_16bit_int(encoder, value) -> int:
    return encoder.add_16bit_int(int(value))


# The various data types that the fronius inverters use
string4 = DataType(4, decode_string4, BinaryPayloadBuilder.add_string)
string8 = DataType(8, decode_string8, BinaryPayloadBuilder.add_string)
string16 = DataType(16, decode_string16, BinaryPayloadBuilder.add_string)

int16 = DataType(1, BinaryPayloadDecoder.decode_16bit_int, encode_16bit_int)
uint16 = DataType(1, BinaryPayloadDecoder.decode_16bit_uint, encode_16bit_int)
bitfield16 = DataType(1, BinaryPayloadDecoder.decode_16bit_uint, encode_16bit_int)
sunssf = DataType(1, BinaryPayloadDecoder.decode_16bit_int, encode_16bit_int)
pad = DataType(1, BinaryPayloadDecoder.decode_16bit_uint, encode_16bit_int)
enum16 = DataType(1, BinaryPayloadDecoder.decode_16bit_uint, encode_16bit_int)
count = DataType(1, BinaryPayloadDecoder.decode_16bit_uint, encode_16bit_int)

int32 = DataType(2, BinaryPayloadDecoder.decode_32bit_int, BinaryPayloadBuilder.add_32bit_int)
acc32 = DataType(2, BinaryPayloadDecoder.decode_32bit_int, BinaryPayloadBuilder.add_32bit_int)

uint32 = DataType(2, BinaryPayloadDecoder.decode_32bit_uint, BinaryPayloadBuilder.add_32bit_uint)
float32 = DataType(
    2, BinaryPayloadDecoder.decode_32bit_float, BinaryPayloadBuilder.add_32bit_float
)
bitfield32 = DataType(
    2, BinaryPayloadDecoder.decode_32bit_float, BinaryPayloadBuilder.add_32bit_float
)

uint64 = DataType(4, BinaryPayloadDecoder.decode_64bit_uint, BinaryPayloadBuilder.add_64bit_uint)
acc64 = DataType(4, BinaryPayloadDecoder.decode_64bit_uint, BinaryPayloadBuilder.add_64bit_uint)


class RegisterReadError(Exception):
    pass


# Fronius modbus register object.
#
# the 'spreadsheet' refers to the various spreadsheets in the 'gen24-modbus-api-external-docs.zip'
# file, available by going to https://www.fronius.com/en/photovoltaics/downloads and searching for
# 'gen24 modbus'
#


# Constructor parameters:
#   address: address as specified in the spreadsheet
#   datatype: One of the above datatypes, as specified for the address in the spreadsheet
#   unit: the modbus unit, either '1' for the fronius inverter or 200 for the attached fronius
#         smart meter.
#   description: free text to describe the register's purpose
class FroniusReg:
    def __init__(self, address, datatype, unit, description):
        self.address = address
        self.datatype = datatype
        self.unit = unit
        self.description = description

    def get(self, modbus_client):
        return self.__get_register_value(modbus_client)

    def set(self, modbus_client, value):
        return self._set_register_value(modbus_client, value)

    def __get_register_value(self, modbus_client):
        modbus_value = modbus_client.read_holding_registers(
            self.address - 1, self.datatype.width, slave=self.unit
        )
        if modbus_value.isError():
            raise RegisterReadError(
                "Unable to read from Fronius Register: %d, %s\n%s"
                % (self.address, self.description, modbus_value)
            )
        if modbus_value is None:
            raise RegisterReadError("It's NONE!")
        return self.datatype.decode_from_register(modbus_value.registers)

    def _set_register_value(self, modbus_client, value):
        modbus_value = modbus_client.write_registers(
            self.address - 1,
            self.datatype.encode_to_buffer(value),
            slave=self.unit,
            skip_encode=True,
        )
        return modbus_value


class ScaledFroniusReg:
    def __init__(self, value_register: FroniusReg, scale_register: FroniusReg):
        "A nicer way of dealing with scaled registers"
        self.value_register = value_register
        self.scale_register = scale_register

    def get(self, modbus_client: ModbusBaseClient) -> float:
        "Return the value_register's value, scaled by scale_register."
        return self.value_register.get(modbus_client) * 10 ** self.scale_register.get(
            modbus_client
        )

    def set(self, modbus_client: ModbusBaseClient, value: [int, float, str]):
        return self.value_register.set(
            modbus_client,
            value / 10 ** self.scale_register.get(modbus_client),
        )
