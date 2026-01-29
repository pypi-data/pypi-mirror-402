from dataclasses import dataclass, field
from typing import Self

from ..cell import Builder, Slice
from .tlb import TlbConstructor
from .compute_skip_reason import ComputeSkipReason, compute_skip_reason


@dataclass(frozen=True, slots=True)
class TrComputePhaseSkipped(TlbConstructor):
    '''
    tr_phase_compute_skipped$0 reason:ComputeSkipReason
        = TrComputePhase;
    '''
    reason: ComputeSkipReason

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return 0b0, 1

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        reason = s.load_tlb(compute_skip_reason)
        return cls(reason)

    def serialize_fields(self, b: Builder) -> Builder:
        return b.store_tlb(self.reason)


@dataclass(frozen=True, slots=True)
class TrComputePhaseVM(TlbConstructor):
    '''
    tr_phase_compute_vm$1 success:Bool msg_state_used:Bool 
        account_activated:Bool gas_fees:Grams
        ^[ gas_used:(VarUInteger 7)
        gas_limit:(VarUInteger 7) gas_credit:(Maybe (VarUInteger 3))
        mode:int8 exit_code:int32 exit_arg:(Maybe int32)
        vm_steps:uint32
        vm_init_state_hash:bits256 vm_final_state_hash:bits256 ]
        = TrComputePhase;
    '''
    success: bool
    msg_state_used: bool
    account_activated: bool
    gas_fees: int
    gas_used: int
    gas_limit: int
    gas_credit: int | None
    mode: int
    exit_code: int
    exit_arg: int | None
    vm_steps: int
    vm_init_state_hash: bytes = field(repr=False)
    vm_final_state_hash: bytes = field(repr=False)

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return 0b1, 1

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        success = s.load_bool()
        msg_state_used = s.load_bool()
        account_activated = s.load_bool()
        gas_fees = s.load_coins()
        s = s.load_ref().begin_parse()
        gas_used = s.load_var_uint(7)
        gas_limit = s.load_var_uint(7)
        gas_credit: int | None = None
        if s.load_bool():
            gas_credit = s.load_var_uint(3)
        mode = s.load_int(8)
        exit_code = s.load_int(32)
        exit_arg: int | None = None
        if s.load_bool():
            exit_arg = s.load_int(32)
        vm_steps = s.load_uint(32)
        vm_init_state_hash = s.load_bytes(32)
        vm_final_state_hash = s.load_bytes(32)
        return cls(success, msg_state_used, account_activated,
                   gas_fees, gas_used, gas_limit, gas_credit,
                   mode, exit_code, exit_arg, vm_steps,
                   vm_init_state_hash, vm_final_state_hash)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_bool(self.success)
        b.store_bool(self.msg_state_used)
        b.store_bool(self.account_activated)
        b.store_coins(self.gas_fees)
        extra = Builder()
        extra.store_var_uint(self.gas_used, 7)
        extra.store_var_uint(self.gas_limit, 7)
        extra.store_bool(self.gas_credit is not None)
        if self.gas_credit is not None:
            extra.store_var_uint(self.gas_credit, 3)
        extra.store_int(self.mode, 8)
        extra.store_int(self.exit_code, 32)
        extra.store_bool(self.exit_arg is not None)
        if self.exit_arg is not None:
            extra.store_int(self.exit_arg, 32)
        extra.store_uint(self.vm_steps, 32)
        extra.store_bytes(self.vm_init_state_hash)
        extra.store_bytes(self.vm_final_state_hash)
        b.store_ref(extra.end_cell())
        return b

TrComputePhase = TrComputePhaseSkipped | TrComputePhaseVM

def tr_compute_phase(s: Slice) -> TrComputePhase:
    b = s.preload_bit()
    match b:
        case 0: return TrComputePhaseSkipped.deserialize(s)
        case 1: return TrComputePhaseVM.deserialize(s)
    assert False
