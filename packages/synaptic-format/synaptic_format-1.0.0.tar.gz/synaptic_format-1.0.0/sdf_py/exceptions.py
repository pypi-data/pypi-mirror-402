# sdf_py/exceptions.py
class SDFException(Exception):
    """Base exception for the sdf-py library."""
    pass

class CorruptRecordError(SDFException):
    """Raised when a record's checksum does not match its content."""
    pass

class InvalidSchemaError(SDFException):
    """Raised when the provided schema is invalid."""
    pass

class UnsupportedTypeError(SDFException):
    """Raised when trying to write a data type not supported by SDF."""
    pass