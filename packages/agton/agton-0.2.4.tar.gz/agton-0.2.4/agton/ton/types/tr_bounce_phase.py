from dataclasses import dataclass
from typing import Self

from ..cell import Builder, Slice
from .tlb import TlbConstructor
from .storage_used import StorageUsed


@dataclass(frozen=True, slots=True)
class TrBouncePhaseNegfunds(TlbConstructor):
    '''tr_phase_bounce_negfunds$00 = TrBouncePhase;'''
    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return 0b00, 2

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b

@dataclass(frozen=True, slots=True)
class TrBouncePhaseNofunds(TlbConstructor):
    '''
    tr_phase_bounce_nofunds$01 msg_size:StorageUsed
        req_fwd_fees:Grams = TrBouncePhase;
    '''
    msg_size: StorageUsed
    req_fwd_fees: int

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return 0b01, 2

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        msg_size = s.load_tlb(StorageUsed)
        req_fwd_fees = s.load_coins()
        return cls(msg_size, req_fwd_fees)

    def serialize_fields(self, b: Builder) -> Builder:
        return (
            b
            .store_tlb(self.msg_size)
            .store_coins(self.req_fwd_fees)
        )

@dataclass(frozen=True, slots=True)
class TrBouncePhaseOk(TlbConstructor):
    '''
    tr_phase_bounce_ok$1 msg_size:StorageUsed
        msg_fees:Grams fwd_fees:Grams = TrBouncePhase;
    '''
    msg_size: StorageUsed
    msg_fees: int
    fwd_fees: int

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return 0b1, 1

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        msg_size = s.load_tlb(StorageUsed)
        msg_fees = s.load_coins()
        fwd_fees = s.load_coins()
        return cls(msg_size, msg_fees, fwd_fees)

    def serialize_fields(self, b: Builder) -> Builder:
        return (
            b
            .store_tlb(self.msg_size)
            .store_coins(self.msg_fees)
            .store_coins(self.fwd_fees)
        )

TrBouncePhase = TrBouncePhaseNegfunds | TrBouncePhaseNofunds | TrBouncePhaseOk

def tr_bounce_phase(s: Slice) -> TrBouncePhase:
    b = s.preload_bit()
    if b == 1:
        return TrBouncePhaseOk.deserialize(s)
    tag = s.preload_uint(2)
    match tag:
        case 0b00: return TrBouncePhaseNegfunds.deserialize(s)
        case 0b01: return TrBouncePhaseNofunds.deserialize(s)
    assert False
