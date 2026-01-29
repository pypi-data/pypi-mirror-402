"""
Serializers Core para AILOOS.
Implementa serialización JSON/TOON/VSC con validación de esquemas y conversión automática.
"""

import json
import struct
import hashlib
import base64
from typing import Any, Dict, List, Optional, Union, Tuple, Type, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import numpy as np
from pydantic import BaseModel, ValidationError

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    jsonschema = None
    JSONSCHEMA_AVAILABLE = False

from ..core.logging import get_logger

logger = get_logger(__name__)


class SerializationFormat(Enum):
    """Formatos de serialización soportados."""
    JSON = "json"
    TOON = "toon"  # Typed Object Notation - para arrays uniformes
    VSC = "vsc"    # Vector Serialized Columns - para datos columnar densos


class SerializationError(Exception):
    """Error base para serialización."""
    pass


class ValidationError(SerializationError):
    """Error de validación de esquema."""
    pass


class ConversionError(SerializationError):
    """Error de conversión entre formatos."""
    pass


@dataclass
class SerializationResult:
    """Resultado de serialización."""
    data: bytes
    format: SerializationFormat
    schema_hash: str
    compressed: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DeserializationResult:
    """Resultado de deserialización."""
    data: Any
    format: SerializationFormat
    schema_hash: str
    validated: bool = False
    metadata: Optional[Dict[str, Any]] = None


class BaseSerializer(ABC):
    """Clase base para serializadores."""

    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        self.schema = schema
        self.schema_hash = self._compute_schema_hash(schema) if schema else None

    @abstractmethod
    def serialize(self, data: Any) -> SerializationResult:
        """Serializar datos."""
        pass

    @abstractmethod
    def deserialize(self, data: bytes) -> DeserializationResult:
        """Deserializar datos."""
        pass

    def validate_schema(self, data: Any) -> bool:
        """Validar datos contra esquema."""
        if not self.schema or not JSONSCHEMA_AVAILABLE:
            return True

        try:
            jsonschema.validate(data, self.schema)
            return True
        except jsonschema.ValidationError as e:
            logger.error(f"Schema validation error: {e}")
            return False

    def _compute_schema_hash(self, schema: Dict[str, Any]) -> str:
        """Computar hash del esquema para validación."""
        schema_str = json.dumps(schema, sort_keys=True)
        return hashlib.sha256(schema_str.encode()).hexdigest()[:16]


class JSONSerializer(BaseSerializer):
    """Serializador JSON con validación de esquemas."""

    def serialize(self, data: Any) -> SerializationResult:
        """Serializar a JSON."""
        if not self.validate_schema(data):
            raise ValidationError("Data does not match schema")

        try:
            json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            json_bytes = json_str.encode('utf-8')

            return SerializationResult(
                data=json_bytes,
                format=SerializationFormat.JSON,
                schema_hash=self.schema_hash,
                metadata={"encoding": "utf-8", "size": len(json_bytes)}
            )
        except (TypeError, ValueError) as e:
            raise SerializationError(f"JSON serialization error: {e}")

    def deserialize(self, data: bytes) -> DeserializationResult:
        """Deserializar desde JSON."""
        try:
            json_str = data.decode('utf-8')
            parsed_data = json.loads(json_str)

            validated = self.validate_schema(parsed_data)

            return DeserializationResult(
                data=parsed_data,
                format=SerializationFormat.JSON,
                schema_hash=self.schema_hash,
                validated=validated,
                metadata={"encoding": "utf-8", "size": len(data)}
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise SerializationError(f"JSON deserialization error: {e}")


class TOONSerializer(BaseSerializer):
    """
    TOON (Typed Object Notation) Serializer.
    Optimizado para arrays uniformes y datos estructurados repetitivos.
    Formato binario eficiente para listas de objetos con estructura similar.
    """

    # Códigos de tipo para TOON
    TYPE_CODES = {
        'null': 0x00,
        'bool': 0x01,
        'int8': 0x02,
        'int16': 0x03,
        'int32': 0x04,
        'int64': 0x05,
        'uint8': 0x06,
        'uint16': 0x07,
        'uint32': 0x08,
        'uint64': 0x09,
        'float32': 0x0A,
        'float64': 0x0B,
        'string': 0x0C,
        'bytes': 0x0D,
        'array': 0x0E,
        'object': 0x0F
    }

    def __init__(self, schema: Optional[Dict[str, Any]] = None, compression_threshold: int = 1024):
        super().__init__(schema)
        self.compression_threshold = compression_threshold

    def serialize(self, data: Any) -> SerializationResult:
        """Serializar a TOON."""
        if not self.validate_schema(data):
            raise ValidationError("Data does not match schema")

        try:
            # TOON header: magic bytes + version + flags
            header = b'TOON\x01\x00'  # Magic + version 1.0

            # Serializar datos
            serialized_data = self._serialize_value(data)

            # Compresión opcional para datos grandes
            compressed = len(serialized_data) > self.compression_threshold
            if compressed:
                # Implementar compresión LZ4 o similar
                serialized_data = self._compress_data(serialized_data)
                header += b'\x01'  # Flag de compresión
            else:
                header += b'\x00'  # Sin compresión

            final_data = header + serialized_data

            return SerializationResult(
                data=final_data,
                format=SerializationFormat.TOON,
                schema_hash=self.schema_hash,
                compressed=compressed,
                metadata={
                    "original_size": len(serialized_data),
                    "compressed_size": len(final_data),
                    "compression_ratio": len(serialized_data) / len(final_data) if compressed else 1.0
                }
            )
        except Exception as e:
            raise SerializationError(f"TOON serialization error: {e}")

    def deserialize(self, data: bytes) -> DeserializationResult:
        """Deserializar desde TOON."""
        try:
            if len(data) < 6:
                raise SerializationError("Invalid TOON data: too short")

            # Verificar header
            if not data.startswith(b'TOON\x01\x00'):
                raise SerializationError("Invalid TOON magic bytes")

            compressed = data[5] == 0x01
            payload = data[6:]

            if compressed:
                payload = self._decompress_data(payload)

            # Deserializar datos
            parsed_data, _ = self._deserialize_value(payload, 0)

            validated = self.validate_schema(parsed_data)

            return DeserializationResult(
                data=parsed_data,
                format=SerializationFormat.TOON,
                schema_hash=self.schema_hash,
                validated=validated,
                metadata={
                    "compressed": compressed,
                    "original_size": len(payload),
                    "final_size": len(data)
                }
            )
        except Exception as e:
            raise SerializationError(f"TOON deserialization error: {e}")

    def _serialize_value(self, value: Any) -> bytes:
        """Serializar un valor individual."""
        if value is None:
            return bytes([self.TYPE_CODES['null']])

        elif isinstance(value, bool):
            return bytes([self.TYPE_CODES['bool'], 1 if value else 0])

        elif isinstance(value, int):
            if -128 <= value <= 127:
                return bytes([self.TYPE_CODES['int8']]) + struct.pack('b', value)
            elif -32768 <= value <= 32767:
                return bytes([self.TYPE_CODES['int16']]) + struct.pack('h', value)
            elif -2147483648 <= value <= 2147483647:
                return bytes([self.TYPE_CODES['int32']]) + struct.pack('i', value)
            else:
                return bytes([self.TYPE_CODES['int64']]) + struct.pack('q', value)

        elif isinstance(value, float):
            return bytes([self.TYPE_CODES['float64']]) + struct.pack('d', value)

        elif isinstance(value, str):
            encoded = value.encode('utf-8')
            return bytes([self.TYPE_CODES['string']]) + struct.pack('I', len(encoded)) + encoded

        elif isinstance(value, (bytes, bytearray)):
            return bytes([self.TYPE_CODES['bytes']]) + struct.pack('I', len(value)) + value

        elif isinstance(value, (list, tuple)):
            items = b''.join(self._serialize_value(item) for item in value)
            return bytes([self.TYPE_CODES['array']]) + struct.pack('I', len(value)) + items

        elif isinstance(value, dict):
            items = []
            for k, v in value.items():
                if not isinstance(k, str):
                    raise SerializationError("TOON dict keys must be strings")
                key_bytes = k.encode('utf-8')
                items.append(struct.pack('I', len(key_bytes)) + key_bytes + self._serialize_value(v))

            return bytes([self.TYPE_CODES['object']]) + struct.pack('I', len(value)) + b''.join(items)

        else:
            raise SerializationError(f"Unsupported type for TOON: {type(value)}")

    def _deserialize_value(self, data: bytes, offset: int) -> Tuple[Any, int]:
        """Deserializar un valor individual."""
        type_code = data[offset]
        offset += 1

        if type_code == self.TYPE_CODES['null']:
            return None, offset

        elif type_code == self.TYPE_CODES['bool']:
            return bool(data[offset]), offset + 1

        elif type_code == self.TYPE_CODES['int8']:
            return struct.unpack('b', data[offset:offset+1])[0], offset + 1

        elif type_code == self.TYPE_CODES['int16']:
            return struct.unpack('h', data[offset:offset+2])[0], offset + 2

        elif type_code == self.TYPE_CODES['int32']:
            return struct.unpack('i', data[offset:offset+4])[0], offset + 4

        elif type_code == self.TYPE_CODES['int64']:
            return struct.unpack('q', data[offset:offset+8])[0], offset + 8

        elif type_code == self.TYPE_CODES['float64']:
            return struct.unpack('d', data[offset:offset+8])[0], offset + 8

        elif type_code == self.TYPE_CODES['string']:
            str_len = struct.unpack('I', data[offset:offset+4])[0]
            offset += 4
            return data[offset:offset+str_len].decode('utf-8'), offset + str_len

        elif type_code == self.TYPE_CODES['bytes']:
            bytes_len = struct.unpack('I', data[offset:offset+4])[0]
            offset += 4
            return data[offset:offset+bytes_len], offset + bytes_len

        elif type_code == self.TYPE_CODES['array']:
            array_len = struct.unpack('I', data[offset:offset+4])[0]
            offset += 4
            items = []
            for _ in range(array_len):
                item, offset = self._deserialize_value(data, offset)
                items.append(item)
            return items, offset

        elif type_code == self.TYPE_CODES['object']:
            obj_len = struct.unpack('I', data[offset:offset+4])[0]
            offset += 4
            obj = {}
            for _ in range(obj_len):
                key_len = struct.unpack('I', data[offset:offset+4])[0]
                offset += 4
                key = data[offset:offset+key_len].decode('utf-8')
                offset += key_len
                value, offset = self._deserialize_value(data, offset)
                obj[key] = value
            return obj, offset

        else:
            raise SerializationError(f"Unknown TOON type code: {type_code}")

    def _compress_data(self, data: bytes) -> bytes:
        """Comprimir datos (placeholder - implementar LZ4)."""
        # TODO: Implementar compresión LZ4 real
        return data

    def _decompress_data(self, data: bytes) -> bytes:
        """Descomprimir datos (placeholder - implementar LZ4)."""
        # TODO: Implementar descompresión LZ4 real
        return data


class VSCSerializer(BaseSerializer):
    """
    VSC (Vector Serialized Columns) Serializer.
    Optimizado para datos columnar densos y numéricos.
    Excelente para datasets científicos, ML features, y series temporales.
    """

    def __init__(self, schema: Optional[Dict[str, Any]] = None, chunk_size: int = 8192):
        super().__init__(schema)
        self.chunk_size = chunk_size

    def serialize(self, data: Any) -> SerializationResult:
        """Serializar a VSC."""
        if not self.validate_schema(data):
            raise ValidationError("Data does not match schema")

        try:
            # VSC header: magic bytes + version + flags
            header = b'VSC\x01\x00\x00'  # Magic + version 1.0 + flags

            if isinstance(data, dict) and self._is_columnar_data(data):
                # Datos columnar
                serialized_data = self._serialize_columnar(data)
                header += b'\x01'  # Flag columnar
            else:
                # Datos regulares serializados como columnar si es posible
                columnar_data = self._convert_to_columnar(data)
                serialized_data = self._serialize_columnar(columnar_data)
                header += b'\x02'  # Flag convertido a columnar

            final_data = header + serialized_data

            return SerializationResult(
                data=final_data,
                format=SerializationFormat.VSC,
                schema_hash=self.schema_hash,
                metadata={
                    "data_type": "columnar",
                    "columns": len(data) if isinstance(data, dict) else 1,
                    "size": len(final_data)
                }
            )
        except Exception as e:
            raise SerializationError(f"VSC serialization error: {e}")

    def deserialize(self, data: bytes) -> DeserializationResult:
        """Deserializar desde VSC."""
        try:
            if len(data) < 7:
                raise SerializationError("Invalid VSC data: too short")

            # Verificar header
            if not data.startswith(b'VSC\x01\x00'):
                raise SerializationError("Invalid VSC magic bytes")

            flags = data[5]
            is_columnar = flags & 0x01
            payload = data[7:]

            # Deserializar datos columnar
            parsed_data = self._deserialize_columnar(payload)

            # Convertir de vuelta si es necesario
            if not is_columnar:
                parsed_data = self._convert_from_columnar(parsed_data)

            validated = self.validate_schema(parsed_data)

            return DeserializationResult(
                data=parsed_data,
                format=SerializationFormat.VSC,
                schema_hash=self.schema_hash,
                validated=validated,
                metadata={
                    "data_type": "columnar",
                    "columns": len(parsed_data) if isinstance(parsed_data, dict) else 1
                }
            )
        except Exception as e:
            raise SerializationError(f"VSC deserialization error: {e}")

    def _is_columnar_data(self, data: Any) -> bool:
        """Verificar si los datos ya están en formato columnar."""
        if not isinstance(data, dict):
            return False

        # Verificar que todos los valores sean arrays/listas del mismo tamaño
        lengths = [len(v) if hasattr(v, '__len__') else 0 for v in data.values()]
        return len(set(lengths)) == 1 and lengths[0] > 0

    def _convert_to_columnar(self, data: Any) -> Dict[str, List]:
        """Convertir datos arbitrarios a formato columnar."""
        if isinstance(data, (list, tuple)) and data:
            if isinstance(data[0], dict):
                # Lista de objetos -> columnar
                columns = {}
                for item in data:
                    for key, value in item.items():
                        if key not in columns:
                            columns[key] = []
                        columns[key].append(value)
                return columns
            else:
                # Lista simple -> columna única
                return {"values": list(data)}
        elif isinstance(data, dict):
            # Dict simple -> cada valor como columna de un elemento
            return {k: [v] for k, v in data.items()}
        else:
            # Valor simple -> columna única
            return {"value": [data]}

    def _convert_from_columnar(self, data: Dict[str, List]) -> Any:
        """Convertir datos columnar de vuelta a formato original."""
        if len(data) == 1 and "value" in data:
            # Valor simple
            return data["value"][0] if data["value"] else None
        elif len(data) == 1 and "values" in data:
            # Lista simple
            return data["values"]
        else:
            # Convertir a lista de objetos
            if not data:
                return []

            # Obtener longitud de la primera columna
            first_col = next(iter(data.values()))
            length = len(first_col)

            result = []
            for i in range(length):
                item = {}
                for key, values in data.items():
                    if i < len(values):
                        item[key] = values[i]
                result.append(item)

            return result

    def _serialize_columnar(self, data: Dict[str, List]) -> bytes:
        """Serializar datos en formato columnar."""
        if not data:
            return b''

        # Obtener tipos de datos por columna
        column_types = {}
        for key, values in data.items():
            column_types[key] = self._infer_column_type(values)

        # Serializar metadata de columnas
        metadata = self._serialize_column_metadata(column_types)

        # Serializar datos por columnas
        column_data = b''
        for key, values in data.items():
            col_type = column_types[key]
            column_data += self._serialize_column(key, values, col_type)

        return metadata + column_data

    def _deserialize_columnar(self, data: bytes) -> Dict[str, List]:
        """Deserializar datos en formato columnar."""
        if not data:
            return {}

        # Deserializar metadata
        column_types, offset = self._deserialize_column_metadata(data, 0)

        # Deserializar columnas
        columns = {}
        for col_name, col_type in column_types.items():
            values, offset = self._deserialize_column(data, offset, col_type)
            columns[col_name] = values

        return columns

    def _infer_column_type(self, values: List) -> str:
        """Inferir tipo de datos para una columna."""
        if not values:
            return "null"

        # Verificar tipos
        types = set(type(v).__name__ for v in values if v is not None)

        if len(types) == 1:
            type_name = types.pop()
            if type_name in ['int', 'float']:
                # Verificar si todos son números
                if all(isinstance(v, (int, float, type(None))) for v in values):
                    if any(isinstance(v, float) for v in values if v is not None):
                        return "float64"
                    else:
                        # Verificar rango para elegir precisión
                        max_val = max((abs(v) for v in values if isinstance(v, int)), default=0)
                        if max_val <= 255:
                            return "uint8"
                        elif max_val <= 65535:
                            return "uint16"
                        elif max_val <= 4294967295:
                            return "uint32"
                        else:
                            return "uint64"
            elif type_name == 'str':
                return "string"
            elif type_name == 'bool':
                return "bool"

        return "string"  # Fallback

    def _serialize_column_metadata(self, column_types: Dict[str, str]) -> bytes:
        """Serializar metadata de columnas."""
        metadata = struct.pack('I', len(column_types))
        for name, col_type in column_types.items():
            name_bytes = name.encode('utf-8')
            type_code = self._get_type_code(col_type)
            metadata += struct.pack('II', len(name_bytes), type_code) + name_bytes
        return metadata

    def _deserialize_column_metadata(self, data: bytes, offset: int) -> Tuple[Dict[str, str], int]:
        """Deserializar metadata de columnas."""
        num_columns = struct.unpack('I', data[offset:offset+4])[0]
        offset += 4

        column_types = {}
        for _ in range(num_columns):
            name_len = struct.unpack('I', data[offset:offset+4])[0]
            offset += 4
            type_code = struct.unpack('I', data[offset:offset+4])[0]
            offset += 4
            name = data[offset:offset+name_len].decode('utf-8')
            offset += name_len
            col_type = self._get_type_name(type_code)
            column_types[name] = col_type

        return column_types, offset

    def _serialize_column(self, name: str, values: List, col_type: str) -> bytes:
        """Serializar una columna individual."""
        # Filtrar valores None y crear máscara
        valid_values = []
        null_mask = []

        for v in values:
            if v is None:
                null_mask.append(False)
                valid_values.append(0)  # Placeholder
            else:
                null_mask.append(True)
                valid_values.append(v)

        # Serializar máscara de nulls
        null_mask_bytes = self._serialize_bool_array(null_mask)

        # Serializar valores
        if col_type == "bool":
            value_bytes = self._serialize_bool_array(valid_values)
        elif col_type.startswith("uint") or col_type.startswith("int"):
            value_bytes = self._serialize_int_array(valid_values, col_type)
        elif col_type.startswith("float"):
            value_bytes = self._serialize_float_array(valid_values, col_type)
        elif col_type == "string":
            value_bytes = self._serialize_string_array(valid_values)
        else:
            value_bytes = self._serialize_string_array([str(v) for v in valid_values])

        return null_mask_bytes + value_bytes

    def _deserialize_column(self, data: bytes, offset: int, col_type: str) -> Tuple[List, int]:
        """Deserializar una columna individual."""
        # Deserializar máscara de nulls
        null_mask, offset = self._deserialize_bool_array(data, offset)

        # Deserializar valores
        if col_type == "bool":
            values, offset = self._deserialize_bool_array(data, offset)
        elif col_type.startswith("uint") or col_type.startswith("int"):
            values, offset = self._deserialize_int_array(data, offset, col_type)
        elif col_type.startswith("float"):
            values, offset = self._deserialize_float_array(data, offset, col_type)
        elif col_type == "string":
            values, offset = self._deserialize_string_array(data, offset)
        else:
            str_values, offset = self._deserialize_string_array(data, offset)
            values = str_values  # Mantener como strings

        # Aplicar máscara de nulls
        result = []
        for i, is_valid in enumerate(null_mask):
            if is_valid and i < len(values):
                result.append(values[i])
            else:
                result.append(None)

        return result, offset

    # Métodos auxiliares para serialización de arrays
    def _serialize_bool_array(self, values: List[bool]) -> bytes:
        """Serializar array de booleanos."""
        # Empaquetar 8 bools por byte
        num_bytes = (len(values) + 7) // 8
        result = bytearray(num_bytes)
        for i, val in enumerate(values):
            if val:
                result[i // 8] |= (1 << (i % 8))
        return bytes([len(values)]) + bytes(result)

    def _deserialize_bool_array(self, data: bytes, offset: int) -> Tuple[List[bool], int]:
        """Deserializar array de booleanos."""
        length = data[offset]
        offset += 1
        num_bytes = (length + 7) // 8
        bytes_data = data[offset:offset+num_bytes]
        offset += num_bytes

        result = []
        for i in range(length):
            byte_idx = i // 8
            bit_idx = i % 8
            if byte_idx < len(bytes_data):
                result.append(bool(bytes_data[byte_idx] & (1 << bit_idx)))
            else:
                result.append(False)
        return result, offset

    def _serialize_int_array(self, values: List[int], col_type: str) -> bytes:
        """Serializar array de enteros."""
        format_char = self._get_numpy_format(col_type)
        array = np.array(values, dtype=format_char)
        return array.tobytes()

    def _deserialize_int_array(self, data: bytes, offset: int, col_type: str) -> Tuple[List[int], int]:
        """Deserializar array de enteros."""
        # Asumir que el array ocupa el resto de los datos por columna
        # En implementación real, necesitaríamos saber el tamaño
        format_char = self._get_numpy_format(col_type)
        itemsize = np.dtype(format_char).itemsize
        length = len(data) // itemsize  # Estimación simplificada
        array = np.frombuffer(data[offset:offset + length * itemsize], dtype=format_char)
        return array.tolist(), offset + length * itemsize

    def _serialize_float_array(self, values: List[float], col_type: str) -> bytes:
        """Serializar array de floats."""
        format_char = self._get_numpy_format(col_type)
        array = np.array(values, dtype=format_char)
        return array.tobytes()

    def _deserialize_float_array(self, data: bytes, offset: int, col_type: str) -> Tuple[List[float], int]:
        """Deserializar array de floats."""
        format_char = self._get_numpy_format(col_type)
        itemsize = np.dtype(format_char).itemsize
        length = len(data) // itemsize  # Estimación simplificada
        array = np.frombuffer(data[offset:offset + length * itemsize], dtype=format_char)
        return array.tolist(), offset + length * itemsize

    def _serialize_string_array(self, values: List[str]) -> bytes:
        """Serializar array de strings."""
        # Usar codificación de longitud + datos
        result = b''
        for s in values:
            encoded = s.encode('utf-8')
            result += struct.pack('I', len(encoded)) + encoded
        return result

    def _deserialize_string_array(self, data: bytes, offset: int) -> Tuple[List[str], int]:
        """Deserializar array de strings."""
        # Implementación simplificada - en la práctica necesitaríamos saber cuántas strings
        strings = []
        start = offset
        while offset < len(data):
            try:
                str_len = struct.unpack('I', data[offset:offset+4])[0]
                offset += 4
                if offset + str_len > len(data):
                    break
                s = data[offset:offset+str_len].decode('utf-8')
                strings.append(s)
                offset += str_len
            except:
                break
        return strings, offset

    def _get_type_code(self, col_type: str) -> int:
        """Obtener código numérico para tipo de columna."""
        type_codes = {
            "null": 0, "bool": 1, "uint8": 2, "uint16": 3, "uint32": 4, "uint64": 5,
            "int8": 6, "int16": 7, "int32": 8, "int64": 9,
            "float32": 10, "float64": 11, "string": 12
        }
        return type_codes.get(col_type, 12)  # Default to string

    def _get_type_name(self, type_code: int) -> str:
        """Obtener nombre de tipo desde código numérico."""
        type_names = {
            0: "null", 1: "bool", 2: "uint8", 3: "uint16", 4: "uint32", 5: "uint64",
            6: "int8", 7: "int16", 8: "int32", 9: "int64",
            10: "float32", 11: "float64", 12: "string"
        }
        return type_names.get(type_code, "string")

    def _get_numpy_format(self, col_type: str) -> str:
        """Obtener formato numpy para tipo de columna."""
        formats = {
            "uint8": "u1", "uint16": "u2", "uint32": "u4", "uint64": "u8",
            "int8": "i1", "int16": "i2", "int32": "i4", "int64": "i8",
            "float32": "f4", "float64": "f8"
        }
        return formats.get(col_type, "f8")


# Serializers globales
_json_serializer = None
_toon_serializer = None
_vsc_serializer = None

def get_json_serializer(schema: Optional[Dict[str, Any]] = None) -> JSONSerializer:
    """Obtener instancia global del serializador JSON."""
    global _json_serializer
    if _json_serializer is None or (_json_serializer.schema != schema):
        _json_serializer = JSONSerializer(schema)
    return _json_serializer

def get_toon_serializer(schema: Optional[Dict[str, Any]] = None) -> TOONSerializer:
    """Obtener instancia global del serializador TOON."""
    global _toon_serializer
    if _toon_serializer is None or (_toon_serializer.schema != schema):
        _toon_serializer = TOONSerializer(schema)
    return _toon_serializer

def get_vsc_serializer(schema: Optional[Dict[str, Any]] = None) -> VSCSerializer:
    """Obtener instancia global del serializador VSC."""
    global _vsc_serializer
    if _vsc_serializer is None or (_vsc_serializer.schema != schema):
        _vsc_serializer = VSCSerializer(schema)
    return _vsc_serializer

def get_serializer(format: SerializationFormat, schema: Optional[Dict[str, Any]] = None) -> BaseSerializer:
    """Obtener serializador por formato."""
    if format == SerializationFormat.JSON:
        return get_json_serializer(schema)
    elif format == SerializationFormat.TOON:
        return get_toon_serializer(schema)
    elif format == SerializationFormat.VSC:
        return get_vsc_serializer(schema)
    else:
        raise ValueError(f"Unsupported serialization format: {format}")

def detect_format(data: bytes) -> Optional[SerializationFormat]:
    """Detectar formato de datos serializados."""
    if len(data) < 4:
        return None

    magic = data[:4]
    if magic == b'TOON':
        return SerializationFormat.TOON
    elif magic == b'VSC\x01':
        return SerializationFormat.VSC
    else:
        # Intentar parsear como JSON
        try:
            json.loads(data.decode('utf-8'))
            return SerializationFormat.JSON
        except:
            return None

def convert_format(data: bytes, from_format: SerializationFormat, to_format: SerializationFormat,
                  schema: Optional[Dict[str, Any]] = None) -> SerializationResult:
    """Convertir entre formatos de serialización."""
    # Deserializar desde formato origen
    from_serializer = get_serializer(from_format, schema)
    deserialized = from_serializer.deserialize(data)

    # Serializar a formato destino
    to_serializer = get_serializer(to_format, schema)
    return to_serializer.serialize(deserialized.data)