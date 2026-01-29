from dataclasses import dataclass
from typing import Self

from ..cell import Builder, Slice

from .tlb import TlbConstructor
from .currency_collection import CurrencyCollection
from .account_state import AccountState, account_state

@dataclass(frozen=True, slots=True)
class AccountStorage(TlbConstructor):
    '''
    account_storage$_ last_trans_lt:uint64
        balance:CurrencyCollection state:AccountState 
        = AccountStorage;
    '''
    last_trans_lt: int
    balance: CurrencyCollection
    state: AccountState

    @classmethod
    def tag(cls) -> None:
        return None

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        last_trans_lt = s.load_uint(64)
        balance = s.load_tlb(CurrencyCollection)
        state = s.load_tlb(account_state)
        return cls(last_trans_lt, balance, state)

    def serialize_fields(self, b: Builder) -> Builder:
        return (
            b
            .store_uint(self.last_trans_lt, 64)
            .store_tlb(self.balance)
            .store_tlb(self.state)
        )

