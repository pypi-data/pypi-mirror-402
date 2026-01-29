from enum import Flag, auto
from typing import Tuple

from iolink_utils.exceptions import InvalidEventMemoryAddress, InvalidEventStatusCode
from iolink_utils.octetDecoder.octetDecoder import StatusCodeType2, EventQualifier


class Event:
    class InitState(Flag):
        CLEAR = 0
        QUALIFIER = auto()
        CODE_MSB = auto()
        CODE_LSB = auto()

    def __init__(self):
        self._qualifier: EventQualifier = EventQualifier()
        self._code: int = 0
        self._state = Event.InitState.CLEAR

    def __eq__(self, other):
        if not isinstance(other, Event):
            return NotImplemented
        return (
                self._code == other._code
                and self._qualifier == other._qualifier
                and self._state == other._state
        )

    @property
    def qualifier(self) -> EventQualifier:
        return self._qualifier

    @property
    def code(self) -> int:
        return self._code

    def setQualifier(self, qualifier: EventQualifier):
        self._qualifier = qualifier.copy()
        self._state |= Event.InitState.QUALIFIER

    def setCode(self, value: int):
        self._code = value
        self._state |= Event.InitState.CODE_MSB
        self._state |= Event.InitState.CODE_LSB

    def setCodeMSB(self, value: int):
        self._code = (self._code & 0x00FF) | (value << 8)
        self._state |= Event.InitState.CODE_MSB

    def setCodeLSB(self, value: int):
        self._code = (self._code & 0xFF00) | value
        self._state |= Event.InitState.CODE_LSB

    def isComplete(self) -> bool:
        return self._state == (
                Event.InitState.QUALIFIER
                | Event.InitState.CODE_MSB
                | Event.InitState.CODE_LSB
        )

    def clear(self):
        self._qualifier.set(0)
        self._code = 0
        self._state = Event.InitState.CLEAR

    def copy(self) -> "Event":
        cp = Event()
        cp._qualifier = self._qualifier.copy()
        cp._code = self._code
        cp._state = self._state
        return cp

    def __copy__(self):  # pragma: no cover
        return self.copy()

    def __deepcopy__(self, memo):  # pragma: no cover
        return self.copy()

    def __str__(self):  # pragma: no cover
        return f"Event({self._qualifier}, {self._code})"


# See Table 58 – Event memory
class EventMemory:
    BYTES_PER_EVENT = 3

    def __init__(self):
        self._statusCode: StatusCodeType2 = StatusCodeType2()
        self._events: Tuple[Event, ...] = (
            Event(), Event(), Event(), Event(), Event(), Event()
        )

    def __eq__(self, other):
        if not isinstance(other, EventMemory):
            return NotImplemented

        return (
                self.statusCode == other.statusCode
                and self.events == other.events
        )

    @property
    def statusCode(self) -> StatusCodeType2:
        return self._statusCode

    @property
    def events(self) -> Tuple[Event, ...]:
        return self._events

    def setMemory(self, address: int, value: int):
        if address > 0x12:  # See Table 58 – Event memory
            raise InvalidEventMemoryAddress(f"Address is invalid: {hex(address)} (max 0x12)")

        if address == 0:
            self._statusCode = StatusCodeType2(value)
            if self._statusCode.details == 0:
                raise InvalidEventStatusCode(f"StatusCodeType2 required (details == 1). Got value '{hex(value)}'")
        else:
            eventsByteAddress = address - 1
            eventNumber = int(eventsByteAddress / EventMemory.BYTES_PER_EVENT)
            byteNumber = eventsByteAddress % EventMemory.BYTES_PER_EVENT

            if byteNumber == 0:
                self._events[eventNumber].setQualifier(EventQualifier(value))
            elif byteNumber == 1:
                self._events[eventNumber].setCodeMSB(value)
            elif byteNumber == 2:
                self._events[eventNumber].setCodeLSB(value)

    def clear(self):
        self._statusCode = StatusCodeType2()
        for event in self._events:
            event.clear()

    def isComplete(self) -> bool:
        if self._statusCode.details == 0:
            return False
        # event memory is complete if all active events are complete (have all 3 bytes)
        return all(
            not active or event.isComplete() for active, event in zip(
                (self._statusCode.evt1, self._statusCode.evt2, self._statusCode.evt3,
                 self._statusCode.evt4, self._statusCode.evt5, self._statusCode.evt6), self._events)
        )

    def copy(self) -> "EventMemory":
        new = EventMemory()
        new._statusCode = self._statusCode.copy()
        new._events = tuple(event.copy() for event in self._events)
        return new

    def __copy__(self):  # pragma: no cover
        return self.copy()

    def __deepcopy__(self, memo):  # pragma: no cover
        return self.copy()
