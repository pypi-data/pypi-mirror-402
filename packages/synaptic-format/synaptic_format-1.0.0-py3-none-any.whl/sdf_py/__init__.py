# sdf_py/__init__.py
"""
SDF-PY: The official Python implementation for the Synaptic Data Format.
A modern, efficient, tensor-native data format for AI workloads.
"""
__version__ = "1.0.0"

from .writer import SDFWriter
from .reader import SDFReader
from .exceptions import SDFException, CorruptRecordError, InvalidSchemaError, UnsupportedTypeError

__all__ = [
    "SDFWriter",
    "SDFReader",
    "SDFException",
    "CorruptRecordError",
    "InvalidSchemaError",
    "UnsupportedTypeError",
]