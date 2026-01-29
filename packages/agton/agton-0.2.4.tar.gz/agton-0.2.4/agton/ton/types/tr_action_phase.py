from dataclasses import dataclass, field
from typing import Self

from ..cell import Builder, Slice
from .tlb import TlbConstructor
from .acc_status_change import AccStatusChange, acc_status_change
from .storage_used import StorageUsed

@dataclass(frozen=True, slots=True)
class TrActionPhase(TlbConstructor):
    '''
    tr_phase_action$_ success:Bool valid:Bool no_funds:Bool
        status_change:AccStatusChange
        total_fwd_fees:(Maybe Grams) total_action_fees:(Maybe Grams)
        result_code:int32 result_arg:(Maybe int32) tot_actions:uint16
        spec_actions:uint16 skipped_actions:uint16 msgs_created:uint16 
        action_list_hash:bits256 tot_msg_size:StorageUsed
        = TrActionPhase;
    '''
    success: bool
    valid: bool
    no_funds: bool
    status_change: AccStatusChange
    total_fwd_fees: int | None
    total_action_fees: int | None
    result_code: int
    result_arg: int | None
    tot_actions: int
    spec_actions: int
    skipped_actions: int
    msgs_created: int
    action_list_hash: bytes = field(repr=False)
    tot_msg_size: StorageUsed

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return None

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        success: bool = s.load_bool()
        valid: bool = s.load_bool()
        no_funds: bool = s.load_bool()
        status_change: AccStatusChange = s.load_tlb(acc_status_change)
        total_fwd_fees: int | None = None
        if s.load_bool():
            total_fwd_fees = s.load_coins()
        total_action_fees: int | None = None
        if s.load_bool():
            total_action_fees = s.load_coins()
        result_code: int = s.load_int(32)
        result_arg: int | None = None
        if s.load_bool():
            result_arg = s.load_int(32)
        tot_actions: int = s.load_uint(16)
        spec_actions: int = s.load_uint(16)
        skipped_actions: int = s.load_uint(16)
        msgs_created: int = s.load_uint(16)
        action_list_hash: bytes = s.load_bytes(32)
        tot_msg_size: StorageUsed = s.load_tlb(StorageUsed)
        return cls(success, valid, no_funds, status_change,
                   total_fwd_fees, total_action_fees, result_code, result_arg,
                   tot_actions, spec_actions, skipped_actions, msgs_created,
                   action_list_hash, tot_msg_size)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_bool(self.success)
        b.store_bool(self.valid)
        b.store_bool(self.no_funds)
        b.store_tlb(self.status_change)
        b.store_bool(self.total_fwd_fees is not None)
        if self.total_fwd_fees is not None:
            b.store_coins(self.total_fwd_fees)
        b.store_bool(self.total_action_fees is not None)
        if self.total_action_fees is not None:
            b.store_coins(self.total_action_fees)
        b.store_int(self.result_code, 32)
        b.store_bool(self.result_arg is not None)
        if self.result_arg is not None:
            b.store_int(self.result_arg, 32)
        b.store_uint(self.tot_actions, 16)
        b.store_uint(self.spec_actions, 16)
        b.store_uint(self.skipped_actions, 16)
        b.store_uint(self.msgs_created, 16)
        b.store_bytes(self.action_list_hash)
        b.store_tlb(self.tot_msg_size)
        return b
