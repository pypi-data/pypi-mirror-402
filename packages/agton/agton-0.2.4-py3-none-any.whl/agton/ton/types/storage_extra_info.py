from dataclasses import dataclass
from typing import Self

from ..cell import Builder, Slice
from .tlb import TlbConstructor

@dataclass(frozen=True, slots=True)
class StorageExtraNone(TlbConstructor):
    '''storage_extra_none$000 = StorageExtraInfo;'''
    @classmethod
    def tag(cls) -> tuple[int, int]:
        return 0b000, 3

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b
    
@dataclass(frozen=True, slots=True)
class StorageExtra(TlbConstructor):
    '''storage_extra_info$001 dict_hash:uint256 = StorageExtraInfo;'''
    dict_hash: bytes

    @classmethod
    def tag(cls) -> tuple[int, int]:
        return 0b001, 3

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        dict_hash = s.load_bytes(32)
        return cls(dict_hash)

    def serialize_fields(self, b: Builder) -> Builder:
        return b.store_bytes(self.dict_hash)

StorageExtraInfo = StorageExtra | StorageExtraNone

def storage_extra_info(s: Slice) -> StorageExtraInfo:
    tag = s.preload_uint(3)
    match tag:
        case 0b000: return StorageExtraNone.deserialize(s)
        case 0b001: return StorageExtra.deserialize(s)
    raise ValueError(f"Unexpected tag {tag:03b} for StorageExtraInfo")
