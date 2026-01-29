from dataclasses import dataclass
from typing import Self

from ..cell import Slice, Builder
from .tlb import TlbConstructor


@dataclass(frozen=True, slots=True)
class AccStatusUnchanged(TlbConstructor):
    '''acst_unchanged$0 = AccStatusChange;'''

    @classmethod
    def tag(cls) -> tuple[int, int]:
        return 0b0, 1

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b

@dataclass(frozen=True, slots=True)
class AccStatusFrozen(TlbConstructor):
    '''acst_frozen$10 = AccStatusChange; '''

    @classmethod
    def tag(cls) -> tuple[int, int]:
        return 0b10, 2

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b

@dataclass(frozen=True, slots=True)
class AccStatusDeleted(TlbConstructor):
    '''acst_deleted$11 = AccStatusChange;'''

    @classmethod
    def tag(cls) -> tuple[int, int]:
        return 0b11, 2

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b

AccStatusChange = AccStatusUnchanged | AccStatusFrozen | AccStatusDeleted

def acc_status_change(s: Slice) -> AccStatusChange:
    tag = s.preload_uint(1)
    if tag == 0:
        return AccStatusUnchanged.deserialize(s)
    tag = s.preload_uint(2)
    match tag:
        case 0b10: return AccStatusFrozen.deserialize(s)
        case 0b11: return AccStatusDeleted.deserialize(s)
    assert False
