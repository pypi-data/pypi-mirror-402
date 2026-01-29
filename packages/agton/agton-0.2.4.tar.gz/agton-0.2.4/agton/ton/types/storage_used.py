from dataclasses import dataclass
from typing import Self

from ..cell import Builder, Slice
from .tlb import TlbConstructor

@dataclass(frozen=True, slots=True)
class StorageUsed(TlbConstructor):
    '''storage_used$_ cells:(VarUInteger 7) bits:(VarUInteger 7) = StorageUsed;'''
    cells: int
    bits: int

    @classmethod
    def tag(cls) -> None:
        return None

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        cells = s.load_var_uint(7)
        bits = s.load_var_uint(7)
        return cls(cells, bits)

    def serialize_fields(self, b: Builder) -> Builder:
        return (
            b
            .store_var_uint(self.cells, 7)
            .store_var_uint(self.bits, 7)
        )
