# sdf_py/reader.py
import json
import struct
import zlib
from typing import IO, Any, Dict, Iterator, Tuple

import numpy as np

from .generated import sdf_pb2
from .exceptions import CorruptRecordError, SDFException

# Mappings from Protobuf DType enum to NumPy dtypes
PROTO_TO_DTYPE = {
    sdf_pb2.Tensor.DType.FLOAT32: np.dtype('float32'),
    sdf_pb2.Tensor.DType.FLOAT64: np.dtype('float64'),
    sdf_pb2.Tensor.DType.INT32: np.dtype('int32'),
    sdf_pb2.Tensor.DType.INT64: np.dtype('int64'),
    sdf_pb2.Tensor.DType.UINT8: np.dtype('uint8'),
    sdf_pb2.Tensor.DType.BOOL: np.dtype('bool'),
}

SDF_MAGIC = b'SDF1'

class SDFReader:
    """Reads and iterates over records in a Synaptic Data Format (.sdf) file."""

    def __init__(self, file_path: str):
        self._file_path = file_path
        self._file: IO[bytes] = open(file_path, "rb")
        self.header = self._read_header()
        self.schema = self.header.get("schema", {})
        self.file_metadata = self.header.get("file_metadata", {})

    def _read_header(self) -> Dict:
        """Reads and parses the file header."""
        magic = self._file.read(4)
        if magic != SDF_MAGIC:
            raise SDFException("Not a valid SDF file or unsupported version.")
        
        header_len_bytes = self._file.read(4)
        header_len = struct.unpack('<I', header_len_bytes)[0]
        
        header_bytes = self._file.read(header_len)
        return json.loads(header_bytes.decode('utf-8'))

    def _unpack_value(self, packet: sdf_pb2.SynapticPacket) -> Any:
        """Unpacks a SynapticPacket into a Python value."""
        field = packet.WhichOneof('value')
        
        if field == 'tensor_value':
            tensor_proto = packet.tensor_value
            dtype = PROTO_TO_DTYPE[tensor_proto.dtype]
            shape = tuple(tensor_proto.shape)
            return np.frombuffer(tensor_proto.data_buffer, dtype=dtype).reshape(shape)
        elif field == 'scalar_value':
            scalar_proto = packet.scalar_value
            scalar_field = scalar_proto.WhichOneof('value')
            return getattr(scalar_proto, scalar_field)
        elif field == 'string_value':
            return packet.string_value
        elif field == 'bytes_value':
            return packet.bytes_value
        elif field == 'sequence_value':
            sequence_proto = packet.sequence_value
            timesteps = []
            for timestep_payload in sequence_proto.timesteps:
                timesteps.append(self._unpack_payload(timestep_payload))
            return timesteps
        return None

    def _unpack_payload(self, payload_proto: sdf_pb2.RecordPayload) -> Dict[str, Any]:
        """Unpacks a RecordPayload protobuf message into a Python dictionary."""
        record_data = {}
        for key, packet in payload_proto.fields.items():
            record_data[key] = self._unpack_value(packet)
        return record_data

    def __iter__(self) -> Iterator[Tuple[Dict, Dict]]:
        """Iterates over the records in the file."""
        while True:
            # Read record header: 8 bytes for length, 4 for metadata length
            record_header_bytes = self._file.read(12)
            if not record_header_bytes:
                break # End of file

            record_length, metadata_length = struct.unpack('<QI', record_header_bytes)
            
            # Read the entire record body (metadata + payload + checksum)
            record_body_bytes = self._file.read(record_length)
            
            # Extract parts
            metadata_bytes = record_body_bytes[:metadata_length]
            payload_and_checksum_bytes = record_body_bytes[metadata_length:]
            
            payload_bytes = payload_and_checksum_bytes[:-4]
            checksum_bytes = payload_and_checksum_bytes[-4:]
            
            # Verify checksum
            expected_checksum = struct.unpack('<I', checksum_bytes)[0]
            calculated_checksum = zlib.crc32(metadata_bytes + payload_bytes)
            
            if expected_checksum != calculated_checksum:
                raise CorruptRecordError(f"Checksum mismatch in record at offset {self._file.tell()}")

            # Deserialize
            record_metadata = json.loads(metadata_bytes.decode('utf-8'))
            
            payload_proto = sdf_pb2.RecordPayload()
            payload_proto.ParseFromString(payload_bytes)
            
            record_data = self._unpack_payload(payload_proto)
            
            yield record_data, record_metadata
            
    def close(self):
        """Closes the file."""
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()