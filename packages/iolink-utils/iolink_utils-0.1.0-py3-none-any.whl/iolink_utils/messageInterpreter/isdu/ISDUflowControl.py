from enum import IntEnum
from iolink_utils.exceptions import InvalidFlowControlValue


class FlowControl:
    INVALID_VALUE = 0xFF

    class State(IntEnum):
        Invalid = 0
        Count = 1
        Start = 2
        Idle = 3
        Abort = 4

    def __init__(self, value: int = 0x11):
        self._state = FlowControl.State.Invalid
        self._value = FlowControl.INVALID_VALUE

        # See Table 52 – FlowCTRL definitions
        mappings = [
            (range(0x00, 0x10), FlowControl.State.Count),  # 0x00–0x0F
            ([0x10], FlowControl.State.Start),
            ([0x11, 0x12], FlowControl.State.Idle),
            ([0x1F], FlowControl.State.Abort),
        ]

        for key_range, state in mappings:
            if value in key_range:
                self._state = state
                self._value = value
                return

        raise InvalidFlowControlValue(f"Invalid ISDU FlowControl value: {hex(value)}")

    def __eq__(self, other):
        if not isinstance(other, FlowControl):
            return NotImplemented
        return (
            self._state == other.state and
            self._value == other.value
        )

    @property
    def state(self):
        return self._state

    @property
    def value(self):
        return self._value
    
    def nextCountValue(self) -> int:
        if self._state == FlowControl.State.Count:
            return 0 if self._value >= 15 else self._value + 1
        else:
            return 1  # "Increments beginning with 1 after an ISDU START"

    def copy(self) -> "FlowControl":
        new = FlowControl()
        new._state = self._state
        new._value = self._value
        return new
