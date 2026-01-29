from iolink_utils.exceptions import InvalidISDUService
from iolink_utils.octetDecoder.octetDecoder import IService
from iolink_utils.definitions.iServiceNibble import IServiceNibble
from iolink_utils.messageInterpreter.isdu.ISDU import ISDU
from iolink_utils.exceptions import UnknownISDUError
from iolink_utils.messageInterpreter.isdu.ISDUerrors import IsduError


#
# WRITE
#

class ISDUResponse_WriteResp_M(ISDU):
    _SERVICE_NIBBLE: IServiceNibble = IServiceNibble.D_WriteResp_M

    def __init__(self):
        super().__init__()
        self.errorCode: int = 0
        self.additionalCode: int = 0
        self.isduError: IsduError = IsduError.UNDEFINED

    def _onFinished(self):
        if not self._hasExtendedLength() and len(self._rawData) == 4:
            self.errorCode = int(self._rawData[1])
            self.additionalCode = int(self._rawData[2])
            try:
                self.isduError = IsduError.fromCodes(self.errorCode, self.additionalCode)
            except ValueError:
                raise UnknownISDUError(f"Unknown ISDU error: "
                                       f"errorCode={hex(self.errorCode)} "
                                       f"additionalCode={hex(self.additionalCode)}") from None
        else:
            self._isValid = False

    def data(self) -> dict:
        return {
            'valid': self.isValid,
            'error': f"{self.isduError.name}({hex(self.errorCode)}, {hex(self.additionalCode)})"
        }


class ISDUResponse_WriteResp_P(ISDU):
    _SERVICE_NIBBLE: IServiceNibble = IServiceNibble.D_WriteResp_P

    def __init__(self):
        super().__init__()

    def _onFinished(self):
        if self._hasExtendedLength() or len(self._rawData) != 2:
            self._isValid = False

    def data(self) -> dict:
        return {
            'valid': self.isValid
        }


#
# READ
#

class ISDUResponse_ReadResp_M(ISDU):
    _SERVICE_NIBBLE: IServiceNibble = IServiceNibble.D_ReadResp_M

    def __init__(self):
        super().__init__()
        self.errorCode: int = 0
        self.additionalCode: int = 0
        self.isduError: IsduError = IsduError.UNDEFINED

    def _onFinished(self):
        if not self._hasExtendedLength() and len(self._rawData) == 4:
            self.errorCode = int(self._rawData[1])
            self.additionalCode = int(self._rawData[2])
            try:
                self.isduError = IsduError.fromCodes(self.errorCode, self.additionalCode)
            except ValueError:
                raise UnknownISDUError(f"Unknown ISDU error: "
                                       f"errorCode={hex(self.errorCode)} "
                                       f"additionalCode={hex(self.additionalCode)}") from None
        else:
            self._isValid = False

    def data(self) -> dict:
        return {
            'valid': self.isValid,
            'error': f"{self.isduError.name}({hex(self.errorCode)}, {hex(self.additionalCode)})"
        }


class ISDUResponse_ReadResp_P(ISDU):
    _SERVICE_NIBBLE: IServiceNibble = IServiceNibble.D_ReadResp_P

    def __init__(self):
        super().__init__()

    def _onFinished(self):
        pass

    def data(self) -> dict:
        return {
            'valid': self.isValid,
            'data': self._rawData[2:-1] if self._hasExtendedLength() else self._rawData[1:-1]
        }


def createISDUResponse(iService: IService):
    _req_map = {
        IServiceNibble.D_WriteResp_M: ISDUResponse_WriteResp_M,
        IServiceNibble.D_WriteResp_P: ISDUResponse_WriteResp_P,
        IServiceNibble.D_ReadResp_M: ISDUResponse_ReadResp_M,
        IServiceNibble.D_ReadResp_P: ISDUResponse_ReadResp_P,
    }

    if iService.service not in _req_map:
        raise InvalidISDUService(f"Invalid response nibble: {iService}")

    return _req_map[iService.service]()
