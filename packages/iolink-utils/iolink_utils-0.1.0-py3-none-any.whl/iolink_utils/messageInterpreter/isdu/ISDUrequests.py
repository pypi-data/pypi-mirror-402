from iolink_utils.exceptions import InvalidISDUService
from iolink_utils.octetDecoder.octetDecoder import IService
from iolink_utils.definitions.iServiceNibble import IServiceNibble
from iolink_utils.messageInterpreter.isdu.ISDU import ISDU


#
# WRITE
#

class ISDURequest_Write8bitIdx(ISDU):
    _SERVICE_NIBBLE: IServiceNibble = IServiceNibble.M_WriteReq_8bitIdx

    def __init__(self):
        super().__init__()
        self.index: int = 0

    def _onFinished(self):
        pos = 2 if self._hasExtendedLength() else 1
        self.index = int(self._rawData[pos])

    def data(self) -> dict:
        return {
            'valid': self.isValid,
            'index': self.index,
            'data': self._rawData[3:-1] if self._hasExtendedLength() else self._rawData[2:-1]
        }


class ISDURequest_Write8bitIdxSub(ISDU):
    _SERVICE_NIBBLE: IServiceNibble = IServiceNibble.M_WriteReq_8bitIdxSub

    def __init__(self):
        super().__init__()
        self.index: int = 0
        self.subIndex: int = 0

    def _onFinished(self):
        pos = 2 if self._hasExtendedLength() else 1
        self.index = int(self._rawData[pos])
        self.subIndex = int(self._rawData[pos + 1])

    def data(self) -> dict:
        return {
            'valid': self.isValid,
            'index': self.index,
            'subIndex': self.subIndex,
            'data': self._rawData[4:-1] if self._hasExtendedLength() else self._rawData[3:-1]
        }


class ISDURequest_Write16bitIdxSub(ISDU):
    _SERVICE_NIBBLE: IServiceNibble = IServiceNibble.M_WriteReq_16bitIdxSub

    def __init__(self):
        super().__init__()
        self.index: int = 0
        self.subIndex: int = 0

    def _onFinished(self):
        pos = 2 if self._hasExtendedLength() else 1
        self.index = int.from_bytes(self._rawData[pos:pos + 2], byteorder='big')
        self.subIndex = int(self._rawData[pos + 2])

    def data(self) -> dict:
        return {
            'valid': self.isValid,
            'index': self.index,
            'subIndex': self.subIndex,
            'data': self._rawData[5:-1] if self._hasExtendedLength() else self._rawData[4:-1]
        }


#
# READ
#

class ISDURequest_Read8bitIdx(ISDU):
    _SERVICE_NIBBLE: IServiceNibble = IServiceNibble.M_ReadReq_8bitIdx

    def __init__(self):
        super().__init__()
        self.index: int = 0

    def _onFinished(self):
        if not self._hasExtendedLength() and len(self._rawData) == 3:
            self.index = int(self._rawData[1])
        else:
            self._isValid = False

    def data(self) -> dict:
        return {
            'valid': self.isValid,
            'index': self.index
        }


class ISDURequest_Read8bitIdxSub(ISDU):
    _SERVICE_NIBBLE: IServiceNibble = IServiceNibble.M_ReadReq_8bitIdxSub

    def __init__(self):
        super().__init__()
        self.index: int = 0
        self.subIndex: int = 0

    def _onFinished(self):
        if not self._hasExtendedLength() and len(self._rawData) == 4:
            self.index = int(self._rawData[1])
            self.subIndex = int(self._rawData[2])
        else:
            self._isValid = False

    def data(self) -> dict:
        return {
            'valid': self.isValid,
            'index': self.index,
            'subIndex': self.subIndex
        }


class ISDURequest_Read16bitIdxSub(ISDU):
    _SERVICE_NIBBLE: IServiceNibble = IServiceNibble.M_ReadReq_16bitIdxSub

    def __init__(self):
        super().__init__()
        self.index: int = 0
        self.subIndex: int = 0

    def _onFinished(self):
        if not self._hasExtendedLength() and len(self._rawData) == 5:
            self.index = int.from_bytes(self._rawData[1:3], byteorder='big')
            self.subIndex = int(self._rawData[3])
        else:
            self._isValid = False

    def data(self) -> dict:
        return {
            'valid': self.isValid,
            'index': self.index,
            'subIndex': self.subIndex
        }


def createISDURequest(iService: IService):
    _req_map = {
        IServiceNibble.M_WriteReq_8bitIdx: ISDURequest_Write8bitIdx,
        IServiceNibble.M_WriteReq_8bitIdxSub: ISDURequest_Write8bitIdxSub,
        IServiceNibble.M_WriteReq_16bitIdxSub: ISDURequest_Write16bitIdxSub,
        IServiceNibble.M_ReadReq_8bitIdx: ISDURequest_Read8bitIdx,
        IServiceNibble.M_ReadReq_8bitIdxSub: ISDURequest_Read8bitIdxSub,
        IServiceNibble.M_ReadReq_16bitIdxSub: ISDURequest_Read16bitIdxSub,
    }

    if iService.service not in _req_map:
        raise InvalidISDUService(f"Invalid request nibble: {iService}")

    return _req_map[iService.service]()
