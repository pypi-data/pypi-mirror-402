from dataclasses import dataclass
from typing import Self

from ..cell import Slice, Builder
from .tlb import TlbConstructor
from .state_init import StateInit

'''account_uninit$00 = AccountState;
account_active$1 _:StateInit = AccountState;
account_frozen$01 state_hash:bits256 = AccountState;'''

@dataclass(frozen=True, slots=True)
class UninitAccountState(TlbConstructor):
    '''account_uninit$00 = AccountState;'''
    @classmethod
    def tag(cls) -> tuple[int, int]:
        return 0b00, 2

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b

@dataclass(frozen=True, slots=True)
class ActiveAccountState(TlbConstructor):
    '''account_active$1 _:StateInit = AccountState;'''
    state_init: StateInit

    @classmethod
    def tag(cls) -> tuple[int, int]:
        return 0b1, 1

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        state_init = s.load_tlb(StateInit)
        return cls(state_init)

    def serialize_fields(self, b: Builder) -> Builder:
        return b.store_tlb(self.state_init)

@dataclass(frozen=True, slots=True)
class FrozenAccountState(TlbConstructor):
    '''account_frozen$01 state_hash:bits256 = AccountState;'''
    state_hash: bytes

    @classmethod
    def tag(cls) -> tuple[int, int]:
        return 0b01, 2

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        state_hash = s.load_bytes(32)
        return cls(state_hash)

    def serialize_fields(self, b: Builder) -> Builder:
        return b.store_bytes(self.state_hash)

AccountState = UninitAccountState | ActiveAccountState | FrozenAccountState

def account_state(s: Slice) -> AccountState:
    b = s.preload_bit()
    if b:
        return ActiveAccountState.deserialize(s)
    tag = s.preload_uint(2)
    match tag:
        case 0b00: return UninitAccountState.deserialize(s)
        case 0b01: return FrozenAccountState.deserialize(s)
    raise ValueError(f"Unknown tag {tag:02b} for AccountState")
