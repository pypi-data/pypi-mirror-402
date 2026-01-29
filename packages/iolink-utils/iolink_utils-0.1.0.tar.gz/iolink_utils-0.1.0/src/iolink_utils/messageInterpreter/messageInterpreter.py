from typing import Union

from iolink_utils.octetStreamDecoder.octetStreamDecoderMessages import DeviceMessage, MasterMessage
from iolink_utils.definitions.communicationChannel import CommChannel

from iolink_utils.messageInterpreter.diagnosis.commChannelDiagnosis import CommChannelDiagnosis, \
    TransactionDiagEventMemory, TransactionDiagEventReset
from iolink_utils.messageInterpreter.isdu.commChannelISDU import CommChannelISDU
from iolink_utils.messageInterpreter.isdu.ISDU import ISDU
from iolink_utils.messageInterpreter.page.commChannelPage import CommChannelPage, TransactionPage
from iolink_utils.messageInterpreter.process.commChannelProcess import CommChannelProcess


class MessageInterpreter:
    def __init__(self):
        self._channelHandler = {
            CommChannel.Process: CommChannelProcess(),  # this is not ProcessData! (dummy handler)
            CommChannel.Page: CommChannelPage(),
            CommChannel.Diagnosis: CommChannelDiagnosis(),
            CommChannel.ISDU: CommChannelISDU()
        }
        self._activeChannel: CommChannel = CommChannel.Process

    def _updateActiveChannel(self, channel: Union[None, CommChannel]):
        if channel is not None:
            self._activeChannel = channel

    def processMessage(self, message: Union[MasterMessage, DeviceMessage]) \
            -> Union[None, TransactionPage, TransactionDiagEventMemory, TransactionDiagEventReset, ISDU]:
        self._updateActiveChannel(message.channel())
        return message.dispatch(self._channelHandler[self._activeChannel])

    def reset(self):
        self._activeChannel = CommChannel.Process

        for handler in self._channelHandler.values():
            handler.reset()
