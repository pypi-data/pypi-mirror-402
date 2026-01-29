from dataclasses import dataclass
from typing import Self

from ..cell import Builder, Slice

from .tlb import TlbConstructor
from .storage_used import StorageUsed
from .storage_extra_info import StorageExtraInfo, storage_extra_info


@dataclass(frozen=True, slots=True)
class StorageInfo(TlbConstructor):
    '''
    storage_info$_ used:StorageUsed storage_extra:StorageExtraInfo last_paid:uint32
              due_payment:(Maybe Grams) = StorageInfo;
    '''
    used: StorageUsed
    storage_extra: StorageExtraInfo
    last_paid: int
    due_payment: int | None

    @classmethod
    def tag(cls) -> None:
        return None

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        used = s.load_tlb(StorageUsed)
        storage_extra = s.load_tlb(storage_extra_info)
        last_paid = s.load_uint(32)
        due_payment = s.load_coins() if s.load_bool() else None
        return cls(used, storage_extra, last_paid, due_payment)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_tlb(self.used)
        b.store_tlb(self.storage_extra)
        b.store_uint(self.last_paid, 32)
        b.store_bool(self.due_payment is not None)
        if self.due_payment is not None:
            b.store_coins(self.due_payment)
        return b
