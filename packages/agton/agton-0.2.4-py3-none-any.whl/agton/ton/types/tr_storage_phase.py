from dataclasses import dataclass
from typing import Self

from ..cell import Slice, Builder
from .tlb import TlbConstructor
from .acc_status_change import AccStatusChange, acc_status_change

@dataclass(frozen=True, slots=True)
class TrStoragePhase(TlbConstructor):
    '''
    tr_phase_storage$_ storage_fees_collected:Grams 
        storage_fees_due:(Maybe Grams)
        status_change:AccStatusChange
        = TrStoragePhase;
    '''
    storage_fees_collected: int
    storage_fees_due: int | None
    status_change: AccStatusChange

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return None

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        storage_fees_collected = s.load_coins()
        storage_fees_due: int | None = None
        if s.load_bool():
            storage_fees_due = s.load_coins()
        status_change = s.load_tlb(acc_status_change)
        return cls(storage_fees_collected, storage_fees_due, status_change)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_coins(self.storage_fees_collected)
        b.store_bool(self.storage_fees_due is not None)
        if self.storage_fees_due is not None:
            b.store_coins(self.storage_fees_due)
        b.store_tlb(self.status_change)
        return b
