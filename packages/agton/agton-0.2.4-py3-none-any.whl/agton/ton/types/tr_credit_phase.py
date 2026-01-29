from dataclasses import dataclass
from typing import Self

from ..cell import Builder, Slice
from .tlb import TlbConstructor
from .currency_collection import CurrencyCollection

@dataclass(frozen=True, slots=True)
class TrCreditPhase(TlbConstructor):
    '''
    tr_phase_credit$_ due_fees_collected:(Maybe Grams)
        credit:CurrencyCollection = TrCreditPhase;
    '''
    due_fees_collected: int | None
    credit: CurrencyCollection

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return None

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        due_fees_collected: int | None = None
        if s.load_bool():
            due_fees_collected = s.load_coins()
        credit = s.load_tlb(CurrencyCollection)
        return cls(due_fees_collected, credit)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_bool(self.due_fees_collected is not None)
        if self.due_fees_collected is not None:
            b.store_coins(self.due_fees_collected)
        b.store_tlb(self.credit)
        return b
