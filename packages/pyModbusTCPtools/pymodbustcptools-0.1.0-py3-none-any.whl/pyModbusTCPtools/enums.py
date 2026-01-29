"""Enumerations used by Modbus tools."""

from enum import Enum


class Endian(Enum):
    """Word/byte order for multi-register values."""

    BE = "be"           # Big-endian (Modbus default)
    LE = "le"           # Little-endian (word swap)
    BE_SWAP = "be_swap" # Big-endian with byte swap
    LE_SWAP = "le_swap" # Little-endian with byte swap

class ModbusDataType(Enum):
    INT16 = "int16"
    UINT16 = "uint16"

    INT32 = "int32"
    UINT32 = "uint32"

    INT64 = "int64"
    UINT64 = "uint64"
    
    FLOAT32 = "float32"
    FLOAT64 = "float64"

    @property
    def bits(self):
        return {
            self.INT16: 16,
            self.UINT16: 16,
            self.INT32: 32,
            self.UINT32: 32,
            self.INT64: 64,
            self.UINT64: 64,
            self.FLOAT32: 32,
            self.FLOAT64: 64,
        }[self]

    @property
    def registers(self):
        """Número de registradores Modbus (16 bits) usados."""
        return self.bits // 16

    @property
    def signed(self):
        return self in {
            self.INT16,
            self.INT32,
            self.INT64,
        }

    @property
    def is_float(self):
        return self in {
            self.FLOAT32,
            self.FLOAT64,
        }