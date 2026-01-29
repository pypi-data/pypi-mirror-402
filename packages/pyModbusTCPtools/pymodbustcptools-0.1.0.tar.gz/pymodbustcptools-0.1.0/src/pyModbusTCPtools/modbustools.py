"""
Modbus TCP resilient client with safe read/write operations,
automatic reconnection, backoff strategy and data type conversions.

Supported types:
- INT16 / UINT16
- INT32 / UINT32
- INT64 / UINT64
- FLOAT32
- FLOAT64 (DOUBLE)

Endianness:
- Big Endian
- Little Endian
- Big Endian with byte swap
- Little Endian with byte swap
"""

import logging
import struct
import time
import os
from logging.handlers import RotatingFileHandler

from pyModbusTCP import utils
from pyModbusTCP.client import ModbusClient

from .enums import Endian, ModbusDataType
from .exceptions import (
    ModbusError,
    ModbusConnectionError,
    ModbusProtocolError,
    ModbusReadError,
    ModbusWriteError,
    ModbusConversionError,
)


class ModbusTCPResiliente:
    """Cliente Modbus TCP resiliente com reconexão, backoff e conversões de tipos."""

    def __init__(
        self,
        host,
        port=502,
        unit_id=1,
        timeout=3.0,
        retry_delay=2.0,        # delay inicial
        max_retry_delay=30.0,   # delay máximo
        ping_addr=0,
        ping_count=1,
        log_file="modbus.log",
        console=False,
        logger=None,
        invalid_cache_ttl=600,
        invalid_cache_max=500
    ):
        self.base_retry_delay = retry_delay
        self.max_retry_delay = max_retry_delay
        self.current_retry_delay = retry_delay

        self.ping_addr = ping_addr
        self.ping_count = ping_count
        self.failure_count = 0


        # Cache de endereços inválidos (ex.: Illegal Data Address)
        self.invalid_cache_ttl = float(invalid_cache_ttl)
        self.invalid_cache_max = int(invalid_cache_max)
        self._invalid_addr_cache = {}  # key -> expires_at (epoch)

        # ========== LOG ==========
        self.console = console
        if logger is not None:
            self.logger = logger
        else:
            logger_name = f"ModbusTCP.{host}:{port}"
            self.logger = logging.getLogger(logger_name)
            self.logger.setLevel(logging.INFO)
            # Evita duplicar logs via root logger caso o usuário configure logging global.
            self.logger.propagate = False

            formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

            if log_file:
                abs_log_file = os.path.abspath(log_file)
                has_file_handler = any(
                    isinstance(h, RotatingFileHandler) and getattr(h, "baseFilename", None) == abs_log_file
                    for h in self.logger.handlers
                )
                if not has_file_handler:
                    file_handler = RotatingFileHandler(
                        log_file,
                        maxBytes=1_000_000,
                        backupCount=3
                    )
                    file_handler.setFormatter(formatter)
                    self.logger.addHandler(file_handler)

            if console:
                has_console_handler = any(
                    isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler)
                    for h in self.logger.handlers
                )
                if not has_console_handler:
                    stream_handler = logging.StreamHandler()
                    stream_handler.setFormatter(formatter)
                    self.logger.addHandler(stream_handler)
        self.client = ModbusClient(
            host=host,
            port=port,
            unit_id=unit_id,
            timeout=timeout,
            auto_open=True,
            auto_close=False
        )

    def _log_and_print(self, level, message):
        """Registra mensagem no log e, opcionalmente, imprime no console."""
        if getattr(self, "console", False):
            print(message)
        getattr(self.logger, level)(message)

    def _increase_backoff(self):
        """Aumenta o tempo de retry com estratégia exponencial."""
        self.current_retry_delay = min(
            self.current_retry_delay * 2,
            self.max_retry_delay
        )

    def _reset_backoff(self):
        """Reseta o tempo de retry para o valor base."""
        self.current_retry_delay = self.base_retry_delay

    # ================== INVALID ADDRESS CACHE ==================
    def _cache_key(self, area: str, addr: int, count: int):
        return (area, int(addr), int(count))

    def _is_invalid_cached(self, key):
        exp = self._invalid_addr_cache.get(key)
        if exp is None:
            return False
        if time.time() >= exp:
            self._invalid_addr_cache.pop(key, None)
            return False
        return True

    def _mark_invalid_cached(self, key):
        if key is None:
            return
        now = time.time()
        # drop expired
        for k, exp in list(self._invalid_addr_cache.items()):
            if now >= exp:
                self._invalid_addr_cache.pop(k, None)
        if len(self._invalid_addr_cache) >= self.invalid_cache_max:
            self._invalid_addr_cache.pop(next(iter(self._invalid_addr_cache)), None)
        self._invalid_addr_cache[key] = now + self.invalid_cache_ttl

    def _get_client_state(self, attr: str, default=0):
        v = getattr(self.client, attr, default)
        try:
            return v() if callable(v) else v
        except Exception:
            return default


    def _connect(self):
        """Abre conexão Modbus se ainda não estiver conectada."""
        if self.client.is_open:
            return True

        self._log_and_print("warning", "Tentando conectar ao CLP...")
        if self.client.open():
            self._log_and_print("info", "Conectado ao CLP")
            self.failure_count = 0
            self._reset_backoff()
            return True

        self._log_and_print(
            "error",
            f"Falha na conexão (retry em {self.current_retry_delay:.1f}s)"
        )
        self.failure_count += 1
        self._increase_backoff()
        return False

    def is_connected(self):
        """Verifica conexão ativa via leitura Modbus real."""
        if not self._connect():
            time.sleep(self.current_retry_delay)
            return False

        try:
            test = self.client.read_holding_registers(
                self.ping_addr, self.ping_count
            )
            if test is None:
                raise Exception("Socket morto")

            self.failure_count = 0
            self._reset_backoff()
            return True

        except Exception:
            self._log_and_print(
                "error",
                f"Conexão perdida, reconectando (retry em {self.current_retry_delay:.1f}s)"
            )
            self.client.close()
            self.failure_count += 1
            self._increase_backoff()
            time.sleep(self.current_retry_delay)
            return False

    def close(self):
        """Fecha explicitamente a conexão Modbus."""
        if self.client.is_open:
            self.client.close()
            self._log_and_print("info", "Conexão encerrada")

    def _handle_error(self, exc, context, close_connection=True):
        """Trata erro Modbus padronizado."""
        level = "warning" if isinstance(exc, ModbusProtocolError) else "error"
        self._log_and_print(level, f"{context}: {exc}")

        if close_connection:
            self.client.close()
            self._increase_backoff()

    def _safe_read(self, action, error_msg, cache_key=None):
        if cache_key is not None and self._is_invalid_cached(cache_key):
            raise ModbusProtocolError(f"Endereço em quarentena (provável inexistente): {cache_key}")

        if not self.is_connected():
            raise ModbusConnectionError("Conexão indisponível")

        result = action()
        if result is None:
            last_except = self._get_client_state("last_except", 0)
            last_error = self._get_client_state("last_error", 0)

            if last_except:
                self._mark_invalid_cached(cache_key)
                raise ModbusProtocolError(f"{error_msg} (Modbus exception={last_except})")

            if last_error:
                raise ModbusConnectionError(f"{error_msg} (socket/transport error={last_error})")

            raise ModbusReadError(error_msg)

        return result

    def _safe_write(self, action, error_msg, cache_key=None):
        if cache_key is not None and self._is_invalid_cached(cache_key):
            raise ModbusProtocolError(f"Endereço em quarentena (provável inexistente): {cache_key}")

        if not self.is_connected():
            raise ModbusConnectionError("Conexão indisponível")

        ok = action()
        if not ok:
            last_except = self._get_client_state("last_except", 0)
            last_error = self._get_client_state("last_error", 0)

            if last_except:
                self._mark_invalid_cached(cache_key)
                raise ModbusProtocolError(f"{error_msg} (Modbus exception={last_except})")

            if last_error:
                raise ModbusConnectionError(f"{error_msg} (socket/transport error={last_error})")

            raise ModbusWriteError(error_msg)

        return True

    def read_discrete_inputs_safe(self, addr, count):
        """Lê Discrete Inputs com reconexão automática."""
        try:
            return self._safe_read(
                lambda: self.client.read_discrete_inputs(addr, count),
                "Falha leitura Discrete Inputs",
                cache_key=self._cache_key("di", addr, count)
            )
        except ModbusError as e:
            close_conn = isinstance(e, (ModbusConnectionError, ModbusReadError, ModbusWriteError)) and not isinstance(e, ModbusProtocolError)
            self._handle_error(e, "read_discrete_inputs_safe", close_connection=close_conn)
            return None

    def read_coils_safe(self, addr, count):
        """Lê Coils com reconexão automática."""
        try:
            return self._safe_read(
                lambda: self.client.read_coils(addr, count),
                "Falha leitura Coils",
                cache_key=self._cache_key("c", addr, count)
            )
        except ModbusError as e:
            close_conn = isinstance(e, (ModbusConnectionError, ModbusReadError, ModbusWriteError)) and not isinstance(e, ModbusProtocolError)
            self._handle_error(e, "read_coils_safe", close_connection=close_conn)
            return None

    def write_single_coil_safe(self, addr, value):
        """Escreve Single Coil."""
        try:
            return self._safe_write(
                lambda: self.client.write_single_coil(addr, value),
                "Falha escrita Single Coil",
                cache_key=self._cache_key("c", addr, 1)
            )
        except ModbusError as e:
            close_conn = isinstance(e, (ModbusConnectionError, ModbusReadError, ModbusWriteError)) and not isinstance(e, ModbusProtocolError)
            self._handle_error(e, "write_single_coil_safe", close_connection=close_conn)
            return False

    def write_multiple_coils_safe(self, addr, values):
        """Escreve múltiplas Coils."""
        try:
            return self._safe_write(
                lambda: self.client.write_multiple_coils(addr, values),
                "Falha escrita Multiple Coils",
                cache_key=self._cache_key("c", addr, len(values))
            )
        except ModbusError as e:
            close_conn = isinstance(e, (ModbusConnectionError, ModbusReadError, ModbusWriteError)) and not isinstance(e, ModbusProtocolError)
            self._handle_error(e, "write_multiple_coils_safe", close_connection=close_conn)
            return False

    def read_input_registers_safe(self, addr, count):
        """Lê Input Registers com reconexão automática."""
        try:
            return self._safe_read(
                lambda: self.client.read_input_registers(addr, count),
                "Falha leitura Input Registers",
                cache_key=self._cache_key("ir", addr, count)
            )
        except ModbusError as e:
            close_conn = isinstance(e, (ModbusConnectionError, ModbusReadError, ModbusWriteError)) and not isinstance(e, ModbusProtocolError)
            self._handle_error(e, "read_input_registers_safe", close_connection=close_conn)
            return None

    def read_holding_registers_safe(self, addr, count):
        """Lê Holding Registers com reconexão automática."""
        try:
            return self._safe_read(
                lambda: self.client.read_holding_registers(addr, count),
                "Falha leitura Holding Registers",
                cache_key=self._cache_key("hr", addr, count)
            )
        except ModbusError as e:
            close_conn = isinstance(e, (ModbusConnectionError, ModbusReadError, ModbusWriteError)) and not isinstance(e, ModbusProtocolError)
            self._handle_error(e, "read_holding_registers_safe", close_connection=close_conn)
            return None

    def write_single_register_safe(self, addr, value):
        """Escreve Single Holding Register."""
        try:
            return self._safe_write(
                lambda: self.client.write_single_register(addr, value),
                "Falha escrita Single Register",
                cache_key=self._cache_key("hr", addr, 1)
            )
        except ModbusError as e:
            close_conn = isinstance(e, (ModbusConnectionError, ModbusReadError, ModbusWriteError)) and not isinstance(e, ModbusProtocolError)
            self._handle_error(e, "write_single_register_safe", close_connection=close_conn)
            return False

    def write_multiple_registers_safe(self, addr, values):
        """Escreve múltiplos Holding Registers."""
        try:
            return self._safe_write(
                lambda: self.client.write_multiple_registers(addr, values),
                "Falha escrita Multiple Registers",
                cache_key=self._cache_key("hr", addr, len(values))
            )
        except ModbusError as e:
            close_conn = isinstance(e, (ModbusConnectionError, ModbusReadError, ModbusWriteError)) and not isinstance(e, ModbusProtocolError)
            self._handle_error(e, "write_multiple_registers_safe", close_connection=close_conn)
            return False

    def write_read_multiple_registers_safe(
        self,
        write_addr,
        write_values,
        read_addr,
        read_nb=1
    ):
        """Executa Write/Read Multiple Registers."""
        try:
            return self._safe_read(
                lambda: self.client.write_read_multiple_registers(
                    write_addr,
                    write_values,
                    read_addr,
                    read_nb
                ),
                "Falha Write/Read Multiple Registers"
            )
        except ModbusReadError as e:
            self._handle_error(e, "write_read_multiple_registers_safe")
            return None
        
    def _dtype_register_count(self, dtype: ModbusDataType) -> int:
        """Retorna quantos registradores (16-bit) o tipo ocupa."""
        return dtype.bits // 16

    def read_holding_typed_safe(self, addr, dtype: ModbusDataType, endian=Endian.BE):
        """Lê Holding Register e converte conforme ModbusDataType."""
        count = self._dtype_register_count(dtype)
        regs = self.read_holding_registers_safe(addr, count)
        if regs is None:
            return None
        try:
            if dtype == ModbusDataType.UINT16:
                return int(regs[0])
            if dtype == ModbusDataType.INT16:
                return self._reg_to_int16(regs[0])
            if dtype == ModbusDataType.UINT32:
                return self._regs_to_uint32(regs, endian)
            if dtype == ModbusDataType.INT32:
                return self._regs_to_int32(regs, endian)
            if dtype == ModbusDataType.UINT64:
                return self._regs_to_uint64(regs, endian)
            if dtype == ModbusDataType.INT64:
                return self._regs_to_int64(regs, endian)
            if dtype == ModbusDataType.FLOAT32:
                return self._regs_to_float32(regs, endian)
            if dtype == ModbusDataType.FLOAT64:
                return self._regs_to_float64(regs, endian)
            raise ModbusConversionError(f"Tipo não suportado: {dtype}")
        except ModbusConversionError as exc:
            self._handle_error(exc, f"read_holding_typed_safe[{dtype.value}]")
            return None

    def read_input_typed_safe(self, addr, dtype: ModbusDataType, endian=Endian.BE):
        """Lê Input Register e converte conforme ModbusDataType."""
        count = self._dtype_register_count(dtype)
        regs = self.read_input_registers_safe(addr, count)
        if regs is None:
            return None
        try:
            if dtype == ModbusDataType.UINT16:
                return int(regs[0])
            if dtype == ModbusDataType.INT16:
                return self._reg_to_int16(regs[0])
            if dtype == ModbusDataType.UINT32:
                return self._regs_to_uint32(regs, endian)
            if dtype == ModbusDataType.INT32:
                return self._regs_to_int32(regs, endian)
            if dtype == ModbusDataType.UINT64:
                return self._regs_to_uint64(regs, endian)
            if dtype == ModbusDataType.INT64:
                return self._regs_to_int64(regs, endian)
            if dtype == ModbusDataType.FLOAT32:
                return self._regs_to_float32(regs, endian)
            if dtype == ModbusDataType.FLOAT64:
                return self._regs_to_float64(regs, endian)
            raise ModbusConversionError(f"Tipo não suportado: {dtype}")
        except ModbusConversionError as exc:
            self._handle_error(exc, f"read_input_typed_safe[{dtype.value}]")
            return None

    def write_holding_typed_safe(self, addr, value, dtype: ModbusDataType, endian=Endian.BE):
        """Escreve em Holding Register conforme ModbusDataType."""
        try:
            if dtype == ModbusDataType.UINT16:
                v = int(value)
                if not (0 <= v <= 0xFFFF):
                    raise ModbusConversionError("UINT16 fora do range")
                return self.write_single_register_safe(addr, v)
            if dtype == ModbusDataType.INT16:
                reg = self._int16_to_reg(value)
                return self.write_single_register_safe(addr, reg)
            if dtype == ModbusDataType.UINT32:
                regs = self._uint32_to_regs(value, endian)
                return self.write_multiple_registers_safe(addr, regs)
            if dtype == ModbusDataType.INT32:
                regs = self._int32_to_regs(value, endian)
                return self.write_multiple_registers_safe(addr, regs)
            if dtype == ModbusDataType.UINT64:
                regs = self._uint64_to_regs(value, endian)
                return self.write_multiple_registers_safe(addr, regs)
            if dtype == ModbusDataType.INT64:
                regs = self._int64_to_regs(value, endian)
                return self.write_multiple_registers_safe(addr, regs)
            if dtype == ModbusDataType.FLOAT32:
                regs = self._float32_to_regs(value, endian)
                return self.write_multiple_registers_safe(addr, regs)
            if dtype == ModbusDataType.FLOAT64:
                regs = self._float64_to_regs(value, endian)
                return self.write_multiple_registers_safe(addr, regs)
            raise ModbusConversionError(f"Tipo não suportado: {dtype}")
        except ModbusConversionError as exc:
            self._handle_error(exc, f"write_holding_typed_safe[{dtype.value}]")
            return False

    def read_holding_int16_safe(self, addr):
        """Lê um Inteiro de 16 bits com sinal como um único Holding Register."""
        regs = self.read_holding_registers_safe(addr, 1)
        if regs is None:
            return None

        try:
            return struct.unpack(">h", struct.pack(">H", regs[0]))[0]
        except Exception:
            self._log_and_print(
                "error",
                "Erro conversão INT16 (Holding Register)"
            )
            return None
        
    def _reg_to_int16(self, value):
        """Converte UINT16 em INT16."""
        return utils.get_2comp(value, 16)
    
    def _int16_to_reg(self, value):
        """Converte INT16 em UINT16."""
        if not (-32768 <= value <= 32767):
            raise ModbusConversionError(f"INT16 fora do range: {value}")

        return value & 0xFFFF
    
    def read_input_int16_safe(self, addr):
        """Lê INT16 de Input Register."""
        try:
            regs = self.read_input_registers_safe(addr, 1)
            if regs is None:
                return None

            return self._reg_to_int16(regs[0])

        except ModbusConversionError as e:
            self._handle_error(e, "read_input_int16_safe")
            return None
        
    def write_holding_int16_safe(self, addr, value):
        """Escreve INT16 em Holding Register."""
        try:
            reg = self._int16_to_reg(value)
            return self.write_single_register_safe(addr, reg)

        except ModbusConversionError as e:
            self._handle_error(e, "write_holding_int16_safe")
            return False
    
    def _regs_to_uint32_core(self, regs, endian: Endian):
        """Converte 2 registradores em UINT32 respeitando endian e byte swap."""
        if len(regs) != 2:
            raise ModbusConversionError("UINT32 requer 2 registradores")

        r = list(regs)

        longs = utils.word_list_to_long(
            r,
            big_endian=endian in (Endian.BE, Endian.BE_SWAP)
        )

        value = longs[0]

        if endian in (Endian.BE_SWAP, Endian.LE_SWAP):
            b = value.to_bytes(4, "big")
            b = b[1::-1] + b[3:1:-1]
            value = int.from_bytes(b, "big")

        return value

    def _regs_to_uint32(self, regs, endian: Endian):
        """Wrapper público interno para conversão UINT32 (mantém compatibilidade)."""
        return self._regs_to_uint32_core(regs, endian)

    def _regs_to_int32(self, regs, endian: Endian):
        """Converte 2 registradores em INT32."""
        unsigned = self._regs_to_uint32_core(regs, endian)
        return utils.get_2comp(unsigned, 32)
    
    def _uint32_to_regs_core(self, value, endian: Endian):
        """Converte UINT32 em 2 registradores respeitando endian e byte swap."""
        if not (0 <= value <= 0xFFFFFFFF):
            raise ModbusConversionError("UINT32 fora do range")

        data = value.to_bytes(4, "big")

        if endian in (Endian.BE_SWAP, Endian.LE_SWAP):
            data = data[1::-1] + data[3:1:-1]

        r0, r1 = struct.unpack(">HH", data)

        if endian in (Endian.LE, Endian.LE_SWAP):
            return [r1, r0]

        return [r0, r1]

    def _uint32_to_regs(self, value, endian: Endian):
        """Wrapper público interno para conversão UINT32→regs (mantém compatibilidade)."""
        return self._uint32_to_regs_core(value, endian)

    def _int32_to_regs(self, value, endian: Endian):
        """Converte INT32 em 2 registradores."""
        unsigned = value & 0xFFFFFFFF
        return self._uint32_to_regs_core(unsigned, endian)


    def read_holding_uint32_safe(self, addr, endian=Endian.BE):
        """Lê UINT32 de Holding Register."""
        try:
            regs = self.read_holding_registers_safe(addr, 2)
            if regs is None:
                return None

            return self._regs_to_uint32(regs, endian)

        except ModbusConversionError as e:
            self._handle_error(e, "read_holding_uint32_safe")
            return None

    def write_holding_uint32_safe(self, addr, value, endian=Endian.BE):
        """Escreve UINT32 em Holding Register."""
        try:
            regs = self._uint32_to_regs(value, endian)
            return self.write_multiple_registers_safe(addr, regs)

        except ModbusConversionError as e:
            self._handle_error(e, "write_holding_uint32_safe")
            return False

    def read_holding_int32_safe(self, addr, endian=Endian.BE):
        """Lê INT32 de Holding Register."""
        try:
            regs = self.read_holding_registers_safe(addr, 2)
            if regs is None:
                return None

            return self._regs_to_int32(regs, endian)

        except ModbusConversionError as e:
            self._handle_error(e, "read_holding_int32_safe")
            return None

    def write_holding_int32_safe(self, addr, value, endian=Endian.BE):
        """Escreve INT32 em Holding Register."""
        try:
            regs = self._int32_to_regs(value, endian)
            return self.write_multiple_registers_safe(addr, regs)

        except ModbusConversionError as e:
            self._handle_error(e, "write_holding_int32_safe")
            return False

    def _regs_to_uint64_core(self, regs, endian: Endian):
        """Converte 4 registradores em UINT64 respeitando endian e byte swap."""
        if len(regs) != 4:
            raise ModbusConversionError("UINT64 requer 4 registradores")

        r = list(regs)

        longs = utils.word_list_to_long(
            r,
            big_endian=endian in (Endian.BE, Endian.BE_SWAP)
        )

        value = (longs[0] << 32) | longs[1]

        if endian in (Endian.BE_SWAP, Endian.LE_SWAP):
            b = value.to_bytes(8, "big")
            b = (
                b[1::-1] + b[3:1:-1] +
                b[5:3:-1] + b[7:5:-1]
            )
            value = int.from_bytes(b, "big")

        return value

    def _regs_to_uint64(self, regs, endian: Endian):
        """Wrapper público interno para conversão UINT64 (mantém compatibilidade)."""
        return self._regs_to_uint64_core(regs, endian)

    def _regs_to_int64(self, regs, endian: Endian):
        """Converte 4 registradores em INT64."""
        unsigned = self._regs_to_uint64(regs, endian)
        return utils.get_2comp(unsigned, 64)

    def _uint64_to_regs_core(self, value, endian: Endian):
        """Converte UINT64 em 4 registradores respeitando endian e byte swap."""
        if not (0 <= value <= 0xFFFFFFFFFFFFFFFF):
            raise ModbusConversionError("UINT64 fora do range")

        data = value.to_bytes(8, "big")

        if endian in (Endian.BE_SWAP, Endian.LE_SWAP):
            data = (
                data[1::-1] + data[3:1:-1] +
                data[5:3:-1] + data[7:5:-1]
            )

        high = int.from_bytes(data[:4], "big")
        low = int.from_bytes(data[4:], "big")

        regs = utils.long_list_to_word([high, low])

        if endian in (Endian.LE, Endian.LE_SWAP):
            return [regs[3], regs[2], regs[1], regs[0]]

        return regs

    def _uint64_to_regs(self, value, endian: Endian):
        """Wrapper público interno para conversão UINT64→regs (mantém compatibilidade)."""
        return self._uint64_to_regs_core(value, endian)

    def _int64_to_regs(self, value, endian: Endian):
        """Converte INT64 em 4 registradores."""
        unsigned = value & 0xFFFFFFFFFFFFFFFF
        return self._uint64_to_regs_core(unsigned, endian)

    def read_holding_uint64_safe(self, addr, endian=Endian.BE):
        """Lê UINT64 de Holding Register."""
        try:
            regs = self.read_holding_registers_safe(addr, 4)
            if regs is None:
                return None

            return self._regs_to_uint64(regs, endian)

        except ModbusConversionError as e:
            self._handle_error(e, "read_holding_uint64_safe")
            return None

    def write_holding_uint64_safe(self, addr, value, endian=Endian.BE):
        """Escreve UINT64 em Holding Register."""
        try:
            regs = self._uint64_to_regs(value, endian)
            return self.write_multiple_registers_safe(addr, regs)

        except ModbusConversionError as e:
            self._handle_error(e, "write_holding_uint64_safe")
            return False

    def read_holding_int64_safe(self, addr, endian=Endian.BE):
        """Lê INT64 de Holding Register."""
        try:
            regs = self.read_holding_registers_safe(addr, 4)
            if regs is None:
                return None

            return self._regs_to_int64(regs, endian)

        except ModbusConversionError as e:
            self._handle_error(e, "read_holding_int64_safe")
            return None

    def write_holding_int64_safe(self, addr, value, endian=Endian.BE):
        """Escreve INT64 em Holding Register."""
        try:
            regs = self._int64_to_regs(value, endian)
            return self.write_multiple_registers_safe(addr, regs)

        except ModbusConversionError as e:
            self._handle_error(e, "write_holding_int64_safe")
            return False

    def _regs_to_float32(self, regs, endian: Endian):
        """Converte 2 registradores em FLOAT32."""
        try:
            value = self._regs_to_uint32_core(regs, endian)
            return utils.decode_ieee(value)
        except Exception as exc:
            raise ModbusConversionError("Falha conversão FLOAT32") from exc


    def _float32_to_regs(self, value, endian: Endian):
        """Converte FLOAT32 em 2 registradores."""
        try:
            encoded = utils.encode_ieee(float(value))
        except Exception as exc:
            raise ModbusConversionError("Valor inválido para FLOAT32") from exc

        return self._uint32_to_regs_core(encoded, endian)

    def read_holding_float32_safe(self, addr, endian=Endian.BE):
        """Lê FLOAT32 de Holding Register."""
        try:
            regs = self.read_holding_registers_safe(addr, 2)
            if regs is None:
                return None

            return self._regs_to_float32(regs, endian)

        except ModbusConversionError as exc:
            self._handle_error(exc, "read_holding_float32_safe")
            return None

    def read_input_float32_safe(self, addr, endian=Endian.BE):
        """Lê FLOAT32 de Input Register."""
        try:
            regs = self.read_input_registers_safe(addr, 2)
            if regs is None:
                return None

            return self._regs_to_float32(regs, endian)

        except ModbusConversionError as exc:
            self._handle_error(exc, "read_input_float32_safe")
            return None

    def write_holding_float32_safe(self, addr, value, endian=Endian.BE):
        """Escreve FLOAT32 em Holding Register."""
        try:
            regs = self._float32_to_regs(value, endian)
            return self.write_multiple_registers_safe(addr, regs)

        except ModbusConversionError as exc:
            self._handle_error(exc, "write_holding_float32_safe")
            return False

    def _regs_to_float64(self, regs, endian: Endian):
        """Converte 4 registradores em FLOAT64 (DOUBLE)."""
        try:
            value = self._regs_to_uint64_core(regs, endian)
            return utils.decode_ieee(value, double=True)
        except Exception as exc:
            raise ModbusConversionError("Falha conversão FLOAT64") from exc

    def _float64_to_regs(self, value, endian: Endian):
        """Converte FLOAT64 (DOUBLE) em 4 registradores."""
        try:
            encoded = utils.encode_ieee(float(value), double=True)
        except Exception as exc:
            raise ModbusConversionError("Valor inválido para FLOAT64") from exc

        return self._uint64_to_regs_core(encoded, endian)

    def read_holding_float64_safe(self, addr, endian=Endian.BE):
        """Lê FLOAT64 (DOUBLE) de Holding Register."""
        try:
            regs = self.read_holding_registers_safe(addr, 4)
            if regs is None:
                return None

            return self._regs_to_float64(regs, endian)

        except ModbusConversionError as exc:
            self._handle_error(exc, "read_holding_float64_safe")
            return None

    def read_input_float64_safe(self, addr, endian=Endian.BE):
        """Lê FLOAT64 (DOUBLE) de Input Register."""
        try:
            regs = self.read_input_registers_safe(addr, 4)
            if regs is None:
                return None

            return self._regs_to_float64(regs, endian)

        except ModbusConversionError as exc:
            self._handle_error(exc, "read_input_float64_safe")
            return None

    def write_holding_float64_safe(self, addr, value, endian=Endian.BE):
        """Escreve FLOAT64 (DOUBLE) em Holding Register."""
        try:
            regs = self._float64_to_regs(value, endian)
            return self.write_multiple_registers_safe(addr, regs)

        except ModbusConversionError as exc:
            self._handle_error(exc, "write_holding_float64_safe")
            return False
