from datetime import datetime as dt
from typing import Union
from abc import ABC, abstractmethod

from iolink_utils.definitions.communicationChannel import CommChannel
from iolink_utils.octetDecoder.octetDecoder import MC, CKT, CKS


class Message(ABC):
    def __init__(self):
        self.startTime: dt = dt(1970, 1, 1)
        self.endTime: dt = dt(1970, 1, 1)
        self.isValid: bool = False

    @abstractmethod
    def dispatch(self, handler):  # pragma: no cover
        pass

    @abstractmethod
    def channel(self) -> Union[None, CommChannel]:  # pragma: no cover
        pass


class MasterMessage(Message):
    def __init__(self):
        super().__init__()

        self.mc: MC = MC()
        self.ckt: CKT = CKT()
        self.pdOut: bytearray = bytearray()
        self.od: bytearray = bytearray()

    def __repr__(self):  # pragma: no cover
        elements = []
        if not self.isValid:
            elements.append('ERR')
        elements.extend([f"mc={self.mc}", f"ckt={self.ckt}"])
        if self.pdOut:
            elements.append(f"pdOut={bytes(self.pdOut).hex()}")
        if self.od:
            elements.append(f"od={bytes(self.od).hex()}")
        return f"MasterMessage({', '.join(elements)})"

    def dispatch(self, handler):
        return handler.handleMasterMessage(self)

    def channel(self):
        return CommChannel(self.mc.channel)


class DeviceMessage(Message):
    def __init__(self):
        super().__init__()

        self.od: bytearray = bytearray()
        self.pdIn: bytearray = bytearray()
        self.cks: CKS = CKS()

    def __repr__(self):  # pragma: no cover
        elements = []
        if not self.isValid:
            elements.append('ERR')
        if self.od:
            elements.append(f"od={bytes(self.od).hex()}")
        if self.pdIn:
            elements.append(f"pdIn={bytes(self.pdIn).hex()}")
        elements.append(f"cks={self.cks}")
        return f"DeviceMessage({', '.join(elements)})"

    def dispatch(self, handler):
        return handler.handleDeviceMessage(self)

    def channel(self) -> Union[None, CommChannel]:
        return None
