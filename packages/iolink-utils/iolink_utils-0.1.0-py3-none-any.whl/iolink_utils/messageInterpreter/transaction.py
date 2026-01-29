from typing import Dict
from abc import ABC, abstractmethod
from datetime import datetime as dt


class Transaction(ABC):
    def __init__(self):
        self.startTime: dt = dt(1970, 1, 1)
        self.endTime: dt = dt(1970, 1, 1)

    def setTime(self, start: dt, end: dt):
        self.startTime = start
        self.endTime = end

    @abstractmethod
    def data(self) -> Dict:  # pragma: no cover
        return {}

    @abstractmethod
    def dispatch(self, handler):  # pragma: no cover
        pass
