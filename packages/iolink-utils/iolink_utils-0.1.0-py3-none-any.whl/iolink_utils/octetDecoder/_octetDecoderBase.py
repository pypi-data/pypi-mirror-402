import ctypes
from typing import Optional
from iolink_utils.exceptions import InvalidOctetValue


class OctetDecoderBase(ctypes.BigEndianStructure):
    """Base class for octet decoder (decoding a single byte)"""
    _pack_ = 1

    def __init__(self, value: Optional[int] = None, **kwargs):
        super().__init__()

        self.set(value if value is not None else 0)  # can be overridden by explicit field ctor parameters

        field_names = {name for name, *_ in getattr(self, "_fields_", [])}
        for key, val in kwargs.items():
            if key not in field_names:
                raise TypeError(f"Unknown field '{key}' for {self.__class__.__name__}")
            setattr(self, key, val)

    def __int__(self):
        """Get underlying integer value (octet) when casting instance (e.g. int(myDecoder)"""
        return int.from_bytes(bytes(self), "big")

    def __eq__(self, other):
        return int(self) == int(other)

    def get(self) -> int:
        """Get octet as integer value"""
        return int(self)

    def set(self, value: int):
        """
        Set the underlying byte (octet) value.

        Parameters
        ----------
        value : int
            An integer between 0 and 255 representing the new byte value.

        Raises
        ------
        InvalidOctetValue
            If `value` is outside the valid byte range (0–255).
        """
        _MAX_OCTET_VALUE = 255
        if 0 <= value <= _MAX_OCTET_VALUE:
            ctypes.memmove(ctypes.addressof(self), ctypes.byref(ctypes.c_uint8(value)), 1)
        else:
            raise InvalidOctetValue()

    def copy(self):
        return self.__class__(int(self))

    def valuesAsString(self) -> str:
        return ", ".join(f"{name}={getattr(self, name)}" for name, *_ in self._fields_ if name != 'unused')

    def __repr__(self):  # pragma: no cover
        """String representation of decoded content."""
        return f"{self.__class__.__name__}({self.valuesAsString()})"
