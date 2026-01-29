from dataclasses import dataclass, field
from typing import Self

from ..cell import Slice, Builder
from .tlb import TlbConstructor

@dataclass(frozen=True, slots=True)
class HashUpdate(TlbConstructor):
    '''
    update_hashes#72 {X:Type} old_hash:bits256 new_hash:bits256
        = HASH_UPDATE X;
    '''
    old_hash: bytes = field(repr=False)
    new_hash: bytes = field(repr=False)

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return 0x72, 8

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        old_hash = s.load_bytes(32)
        new_hash = s.load_bytes(32)
        return cls(old_hash, new_hash)

    def serialize_fields(self, b: Builder) -> Builder:
        return (
            b
            .store_bytes(self.old_hash)
            .store_bytes(self.new_hash)
        )
    