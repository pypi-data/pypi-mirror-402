from typing import Tuple
from enum import Enum, unique

# See Table C.1 – ErrorTypes
@unique
class IsduError(Enum):
    UNDEFINED = (0x00, 0x00)  # not in spec (used as default value)
    APP_DEV = (0x80, 0x00)
    IDX_NOTAVAIL = (0x80, 0x11)
    SUBIDX_NOTAVAIL = (0x80, 0x12)
    SERV_NOTAVAIL = (0x80, 0x20)
    SERV_NOTAVAIL_LOCCTRL = (0x80, 0x21)
    SERV_NOTAVAIL_DEVCTRL = (0x80, 0x22)
    IDX_NOT_ACCESSIBLE = (0x80, 0x23)
    PAR_VALOUTOFRNG = (0x80, 0x30)
    PAR_VALGTLIM = (0x80, 0x31)
    PAR_VALLTLIM = (0x80, 0x32)
    VAL_LENOVRRUN = (0x80, 0x33)
    VAL_LENUNDRUN = (0x80, 0x34)
    FUNC_NOTAVAIL = (0x80, 0x35)
    FUNC_UNAVAILTEMP = (0x80, 0x36)
    PAR_SETINVALID = (0x80, 0x40)
    PAR_SETINCONSIST = (0x80, 0x41)
    APP_DEVNOTRDY = (0x80, 0x82)
    UNSPECIFIC = (0x81, 0x00)

    VENDOR_SPECIFIC = "VENDOR_SPECIFIC"  # range (0x81, 0x01-0xFF) handled in __missing__

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, Tuple) and len(value) == 2:
            errorCode, additionalCode = value
            if errorCode == 0x81 and 0x01 <= additionalCode <= 0xFF:
                return cls.VENDOR_SPECIFIC
        return None

    @classmethod
    def fromCodes(cls, errorCode: int, additionalCode: int) -> "IsduError":
        return cls((errorCode, additionalCode))
