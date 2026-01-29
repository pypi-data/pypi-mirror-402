from iolink_utils.octetStreamDecoder.octetStreamDecoderMessages import DeviceMessage, MasterMessage
from iolink_utils.definitions.transmissionDirection import TransmissionDirection

from .transactionProcess import TransactionProcess


class CommChannelProcess:
    def __init__(self):
        self._direction: TransmissionDirection = TransmissionDirection.Read

    def reset(self) -> None:
        self._direction = TransmissionDirection.Read

    def handleMasterMessage(self, message: MasterMessage):
        self._direction = TransmissionDirection(message.mc.read)

        transaction = TransactionProcess("Master", self._direction)
        transaction.setTime(message.startTime, message.endTime)
        return transaction

    def handleDeviceMessage(self, message: DeviceMessage):
        transaction = TransactionProcess("Device", self._direction)
        transaction.setTime(message.startTime, message.endTime)
        return transaction
