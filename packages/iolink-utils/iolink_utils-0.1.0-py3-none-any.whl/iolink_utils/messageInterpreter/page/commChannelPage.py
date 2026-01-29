from datetime import datetime as dt

from iolink_utils.octetStreamDecoder.octetStreamDecoderMessages import DeviceMessage, MasterMessage
from iolink_utils.definitions.transmissionDirection import TransmissionDirection

from .transactionPage import TransactionPage


class CommChannelPage:
    def __init__(self):
        self._startTime: dt = dt(1970, 1, 1)
        self._endTime: dt = dt(1970, 1, 1)

        self._direction: TransmissionDirection = TransmissionDirection.Read
        self._pageIndex: int = 0
        self._octet: int = 0

    def reset(self) -> None:
        self._direction = TransmissionDirection.Read
        self._pageIndex = 0
        self._octet = 0

    def handleMasterMessage(self, message: MasterMessage) -> None:
        self._startTime = message.startTime
        self._endTime = message.endTime

        self._direction = TransmissionDirection(message.mc.read)
        self._pageIndex = message.mc.address
        self._octet = message.od[0] if self._direction == TransmissionDirection.Write else 0

        return None

    def handleDeviceMessage(self, message: DeviceMessage) -> TransactionPage:
        self._endTime = message.endTime
        if self._direction == TransmissionDirection.Read:
            self._octet = message.od[0]

        transaction = TransactionPage(self._direction, self._pageIndex, int(self._octet))
        transaction.setTime(self._startTime, self._endTime)
        return transaction
