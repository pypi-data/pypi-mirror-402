import abc
import logging
from typing import Any, Sequence

from . import util

logger = logging.getLogger(__name__)


class IHeadAmp(abc.ABC):
    """Abstract Base Class for headamps"""

    def __init__(self, remote, index: int):
        self._remote = remote
        self.index = index + 1
        self.logger = logger.getChild(self.__class__.__name__)

    def getter(self, param: str) -> Sequence[Any]:
        return self._remote.query(f'{self.address}/{param}')

    def setter(self, param: str, val: object) -> None:
        self._remote.send(f'{self.address}/{param}', val)

    @property
    @abc.abstractmethod
    def address(self) -> str:
        raise NotImplementedError


class HeadAmp(IHeadAmp):
    """Concrete class for headamps"""

    @property
    def address(self) -> str:
        return f'/headamp/{str(self.index).zfill(2)}'

    @property
    def gain(self) -> float:
        return round(util.lin_get(-12, 60, self.getter('gain')[0]), 1)

    @gain.setter
    def gain(self, val: float):
        self.setter('gain', util.lin_set(-12, 60, val))

    @property
    def phantom(self) -> bool:
        return self.getter('phantom')[0] == 1

    @phantom.setter
    def phantom(self, val: bool):
        self.setter('phantom', 1 if val else 0)
