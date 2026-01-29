"""Custom exceptions for Modbus tools."""


class ModbusError(Exception):
    """Base exception for all Modbus-related errors."""


class ModbusConnectionError(ModbusError):
    """Raised when a Modbus connection cannot be established or is lost."""


class ModbusProtocolError(ModbusError):
    """Raised when the Modbus server returns an application/protocol exception
    (e.g., Illegal Data Address), while the TCP connection may still be alive.
    """


class ModbusReadError(ModbusError):
    """Raised when a Modbus read operation fails."""


class ModbusWriteError(ModbusError):
    """Raised when a Modbus write operation fails."""


class ModbusConversionError(ModbusError):
    """Raised when data type conversion fails (INT/FLOAT/Endian)."""
