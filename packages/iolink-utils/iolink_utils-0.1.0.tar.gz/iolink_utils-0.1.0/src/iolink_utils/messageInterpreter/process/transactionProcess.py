from typing import Dict

from iolink_utils.messageInterpreter.transaction import Transaction
from iolink_utils.definitions.transmissionDirection import TransmissionDirection


class TransactionProcess(Transaction):
    def __init__(self, source: str, direction: TransmissionDirection):
        super().__init__()

        self.direction: TransmissionDirection = direction
        self.source: str = source

    def data(self) -> Dict:
        return {
            'processDir': self.direction,
            'processSource': self.source
        }

    def dispatch(self, handler):
        return handler.handleProcess(self)

    def __str__(self):  # pragma: no cover
        return f"Process {self.direction}: {self.source}"
