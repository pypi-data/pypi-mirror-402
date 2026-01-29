from typing import Dict
from datetime import datetime as dt

from iolink_utils.messageInterpreter.transaction import Transaction
from iolink_utils.definitions.transmissionDirection import TransmissionDirection
from iolink_utils.utils.directParameterTranslator import translateDirectParameter, Translation


class TransactionPage(Transaction):
    def __init__(self, direction: TransmissionDirection, pageIndex: int, value: int):
        super().__init__()

        self.direction: TransmissionDirection = direction
        self.index: int = pageIndex
        self.value: int = value

    def setTime(self, start: dt, end: dt):
        self.startTime = start
        self.endTime = end

    def data(self) -> Dict:
        translation: Translation = translateDirectParameter(self.index, self.value, self.direction)
        return {
            'pageDir': self.direction.name,
            'pageIndex': str(self.index),
            'pageValue': f'0x{self.value:02X}',
            'pageInfo': f'{translation.name}: {translation.value}',
            'pageError': translation.error
        }

    def dispatch(self, handler):
        return handler.handlePage(self)

    def __str__(self):  # pragma: no cover
        translation: Translation = translateDirectParameter(self.index, self.value, self.direction)
        return f"Page {self.direction.name}: {': '.join(filter(None, translation))}"
