from csp_lib.modbus.enums import ByteOrder, RegisterOrder
from csp_lib.modbus.types.base import ModbusDataType
from typing import Any

__all__ = ['ModbusCodec']

class ModbusCodec:
    def encode(self, data_type: ModbusDataType, value: Any, byte_order: ByteOrder | None = ..., register_order: RegisterOrder | None = ...) -> list[int]: ...
    def decode(self, data_type: ModbusDataType, registers: list[int], byte_order: ByteOrder | None = ..., register_order: RegisterOrder | None = ...) -> Any: ...
