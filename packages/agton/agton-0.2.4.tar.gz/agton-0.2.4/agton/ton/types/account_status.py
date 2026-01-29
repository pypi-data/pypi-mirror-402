from dataclasses import dataclass
from typing import Self

from ..cell import Slice, Builder
from .tlb import TlbConstructor


@dataclass(frozen=True, slots=True)
class AccStateUninit(TlbConstructor):
    '''acc_state_uninit$00 = AccountStatus;'''

    @classmethod
    def tag(cls) -> tuple[int, int]:
        return 0b00, 2

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b

@dataclass(frozen=True, slots=True)
class AccStateFrozen(TlbConstructor):
    '''acc_state_frozen$01 = AccountStatus;'''

    @classmethod
    def tag(cls) -> tuple[int, int]:
        return 0b01, 2

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b

@dataclass(frozen=True, slots=True)
class AccStateActive(TlbConstructor):
    '''acc_state_active$10 = AccountStatus;'''

    @classmethod
    def tag(cls) -> tuple[int, int]:
        return 0b10, 2

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b

@dataclass(frozen=True, slots=True)
class AccStateNonexist(TlbConstructor):
    '''acc_state_nonexist$11 = AccountStatus;'''

    @classmethod
    def tag(cls) -> tuple[int, int]:
        return 0b11, 2

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b

AccountStatus = AccStateUninit | AccStateFrozen | AccStateActive | AccStateNonexist

def account_status(s: Slice) -> AccountStatus:
    tag = s.preload_uint(2)
    match tag:
        case 0b00: return AccStateUninit.deserialize(s)
        case 0b01: return AccStateFrozen.deserialize(s)
        case 0b10: return AccStateActive.deserialize(s)
        case 0b11: return AccStateNonexist.deserialize(s)
    assert False
