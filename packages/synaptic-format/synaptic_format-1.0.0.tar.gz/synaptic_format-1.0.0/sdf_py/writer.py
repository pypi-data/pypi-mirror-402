# sdf_py/writer.py
import json
import struct
import zlib
from typing import IO, Any, Dict, List

import numpy as np
import yaml

# Import generated protobuf classes
from .generated import sdf_pb2
from .exceptions import InvalidSchemaError, UnsupportedTypeError

# Mappings from NumPy dtypes to our Protobuf DType enum
DTYPE_TO_PROTO = {
    np.dtype('float32'): sdf_pb2.Tensor.DType.FLOAT32,
    np.dtype('float64'): sdf_pb2.Tensor.DType.FLOAT64,
    np.dtype('int32'): sdf_pb2.Tensor.DType.INT32,
    np.dtype('int64'): sdf_pb2.Tensor.DType.INT64,
    np.dtype('uint8'): sdf_pb2.Tensor.DType.UINT8,
    np.dtype('bool'): sdf_pb2.Tensor.DType.BOOL,
}

# Magic number to identify SDF files: "SDF" + version 1
SDF_MAGIC = b'SDF1'

class SDFWriter:
    """Writes data records to a Synaptic Data Format (.sdf) file."""

    def __init__(self, file_path: str, schema: Dict, file_metadata: Dict = None):
        self._file_path = file_path
        self._schema = schema
        self._file_metadata = file_metadata or {}
        self._file: IO[bytes] = open(file_path, "wb")
        self._write_header()

    def _write_header(self):
        """Writes the SDF file header containing the schema."""
        header_payload = {
            "version": "1.0",
            "file_metadata": self._file_metadata,
            "schema": self._schema
        }
        # We use YAML for the human-readable part, then serialize to JSON for binary storage
        header_bytes = json.dumps(header_payload, indent=None).encode('utf-8')
        
        # Write Magic Number + Header Length + Header Content
        self._file.write(SDF_MAGIC)
        self._file.write(struct.pack('<I', len(header_bytes)))
        self._file.write(header_bytes)

    def _pack_value(self, value: Any) -> sdf_pb2.SynapticPacket:
        """Packs a Python value into a SynapticPacket."""
        packet = sdf_pb2.SynapticPacket()
        
        if isinstance(value, np.ndarray):
            if value.dtype not in DTYPE_TO_PROTO:
                raise UnsupportedTypeError(f"Unsupported NumPy dtype: {value.dtype}")
            tensor = packet.tensor_value
            tensor.dtype = DTYPE_TO_PROTO[value.dtype]
            tensor.shape.extend(value.shape)
            tensor.data_buffer = value.tobytes()
        elif isinstance(value, (int, np.integer)):
            packet.scalar_value.int_val = value
        elif isinstance(value, (float, np.floating)):
            packet.scalar_value.float_val = value
        elif isinstance(value, bool):
            packet.scalar_value.bool_val = value
        elif isinstance(value, str):
            packet.string_value = value
        elif isinstance(value, bytes):
            packet.bytes_value = value
        elif isinstance(value, list):
            # This is a sequence (e.g., for RL trajectories)
            for timestep_dict in value:
                if not isinstance(timestep_dict, dict):
                    raise UnsupportedTypeError("Sequence elements must be dictionaries.")
                timestep_payload = self._create_payload(timestep_dict)
                packet.sequence_value.timesteps.append(timestep_payload)
        else:
            raise UnsupportedTypeError(f"Unsupported data type: {type(value)}")
            
        return packet

    def _create_payload(self, record_data: Dict[str, Any]) -> sdf_pb2.RecordPayload:
        """Creates a RecordPayload protobuf message from a Python dictionary."""
        payload = sdf_pb2.RecordPayload()
        for key, value in record_data.items():
            payload.fields[key].CopyFrom(self._pack_value(value))
        return payload

    def write(self, record_data: Dict[str, Any], record_metadata: Dict = None):
        """
        Writes a single Synaptic Record to the file.
        
        Args:
            record_data: A dictionary of {field_name: value}.
            record_metadata: An optional dictionary of record-level metadata.
        """
        # 1. Create payload
        payload_proto = self._create_payload(record_data)
        payload_bytes = payload_proto.SerializeToString()

        # 2. Create metadata
        metadata_bytes = json.dumps(record_metadata or {}).encode('utf-8')
        
        # 3. Calculate checksum
        # The checksum is over the combined metadata and payload
        checksum = zlib.crc32(metadata_bytes + payload_bytes)
        
        # 4. Pack and write the record header and content
        # < Q: unsigned long long (8 bytes) for record length
        # < I: unsigned int (4 bytes) for metadata length
        # < I: unsigned int (4 bytes) for checksum
        record_length = len(metadata_bytes) + len(payload_bytes) + 4 # 4 bytes for checksum
        record_header = struct.pack('<QI', record_length, len(metadata_bytes))
        
        self._file.write(record_header)
        self._file.write(metadata_bytes)
        self._file.write(payload_bytes)
        self._file.write(struct.pack('<I', checksum))

    def close(self):
        """Closes the file."""
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()