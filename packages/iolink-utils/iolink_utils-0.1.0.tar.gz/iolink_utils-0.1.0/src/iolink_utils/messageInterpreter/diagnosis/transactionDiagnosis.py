import copy
from typing import Dict
from datetime import datetime as dt

from iolink_utils.definitions.eventInfo import EventType, EventMode
from iolink_utils.definitions.eventMemory import EventMemory
from iolink_utils.messageInterpreter.transaction import Transaction


class TransactionDiagEventMemory(Transaction):
    def __init__(self, startTime: dt, endTime: dt, eventMemory: EventMemory):
        super().__init__()
        self.setTime(startTime, endTime)
        self.eventMemory: EventMemory = copy.deepcopy(eventMemory)

    def _getEvents(self):
        event_flags = [
            self.eventMemory.statusCode.evt1,
            self.eventMemory.statusCode.evt2,
            self.eventMemory.statusCode.evt3,
            self.eventMemory.statusCode.evt4,
            self.eventMemory.statusCode.evt5,
            self.eventMemory.statusCode.evt6,
        ]

        events = []
        for flag, event in zip(event_flags, self.eventMemory.events):
            if flag:
                events.append(f"{EventType(event.qualifier.type).name}"
                              f"{EventMode(event.qualifier.mode).name}"
                              f"(0x{event.code:0{4}X})")
        return events

    def data(self) -> Dict:
        return {
            'eventStatus': self.eventMemory.statusCode.valuesAsString(),
            'events': ", ".join(self._getEvents())
        }

    def dispatch(self, handler):
        return handler.handleDiagEventMemory(self)

    def __str__(self):  # pragma: no cover
        return f"Diag EventMem: '{self.data()}"


class TransactionDiagEventReset(Transaction):
    def __init__(self, startTime: dt, endTime: dt):
        super().__init__()
        self.setTime(startTime, endTime)

    def data(self) -> Dict:
        return {}

    def dispatch(self, handler):
        return handler.handleDiagEventReset(self)

    def __str__(self):  # pragma: no cover
        return "Diag Reset"
