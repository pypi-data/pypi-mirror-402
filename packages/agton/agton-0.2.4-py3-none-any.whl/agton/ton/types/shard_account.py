from dataclasses import dataclass
from typing import Self

from ..cell import Slice, Builder

from .tlb import TlbConstructor
from .account import Account, account

@dataclass(frozen=True, slots=True)
class ShardAccount(TlbConstructor):
    '''
    account_descr$_ account:^Account last_trans_hash:bits256 
        last_trans_lt:uint64 = ShardAccount;
    '''
    account: Account
    last_trans_hash: bytes
    last_trans_lt: int

    @classmethod
    def tag(cls) -> None:
        return None

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        account_ = s.load_ref_tlb(account)
        last_trans_hash = s.load_bytes(32)
        last_trans_lt = s.load_uint(64)
        return cls(account_, last_trans_hash, last_trans_lt)

    def serialize_fields(self, b: Builder) -> Builder:
        return (
            b
            .store_ref_tlb(self.account)
            .store_bytes(self.last_trans_hash)
            .store_uint(self.last_trans_lt, 64)
        )
