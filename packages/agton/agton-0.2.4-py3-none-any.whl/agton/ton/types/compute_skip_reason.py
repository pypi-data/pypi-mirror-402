from dataclasses import dataclass
from typing import Self

from ..cell import Slice, Builder
from .tlb import TlbConstructor


@dataclass(frozen=True, slots=True)
class CSkipNoState(TlbConstructor):
    '''cskip_no_state$00 = ComputeSkipReason;'''

    @classmethod
    def tag(cls) -> tuple[int, int]:
        return 0b00, 2

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b

@dataclass(frozen=True, slots=True)
class CSkipBadState(TlbConstructor):
    '''cskip_bad_state$01 = ComputeSkipReason;'''

    @classmethod
    def tag(cls) -> tuple[int, int]:
        return 0b01, 2

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b

@dataclass(frozen=True, slots=True)
class CSkipNoGas(TlbConstructor):
    '''cskip_no_gas$10 = ComputeSkipReason;'''

    @classmethod
    def tag(cls) -> tuple[int, int]:
        return 0b10, 2

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b

@dataclass(frozen=True, slots=True)
class CSkipSuspended(TlbConstructor):
    '''cskip_suspended$110 = ComputeSkipReason;'''

    @classmethod
    def tag(cls) -> tuple[int, int]:
        return 0b110, 3

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b

ComputeSkipReason = CSkipNoState | CSkipBadState | CSkipNoGas | CSkipSuspended

def compute_skip_reason(s: Slice) -> ComputeSkipReason:
    tag = s.preload_uint(2)
    match tag:
        case 0b00: return CSkipNoState.deserialize(s)
        case 0b01: return CSkipBadState.deserialize(s)
        case 0b10: return CSkipNoGas.deserialize(s)
        case 0b11:
            tag = s.preload_uint(3)
            if tag != 0b110:
                raise ValueError(f'Unexpected tag {tag:03b} for ComputeSkipReason')
            return CSkipSuspended.deserialize(s)
    assert False
