from dataclasses import dataclass
from typing import Self

from ..cell import Slice, Builder
from .tlb import TlbConstructor

from .tr_storage_phase import TrStoragePhase
from .tr_credit_phase import TrCreditPhase
from .tr_compute_phase import TrComputePhase, tr_compute_phase
from .tr_action_phase import TrActionPhase
from .tr_bounce_phase import TrBouncePhase, tr_bounce_phase

'''
trans_ord$0000 credit_first:Bool
    storage_ph:(Maybe TrStoragePhase)
    credit_ph:(Maybe TrCreditPhase)
    compute_ph:TrComputePhase action:(Maybe ^TrActionPhase)
    aborted:Bool bounce:(Maybe TrBouncePhase)
    destroyed:Bool
    = TransactionDescr;

trans_storage$0001 storage_ph:TrStoragePhase
    = TransactionDescr;

trans_tick_tock$001 is_tock:Bool storage_ph:TrStoragePhase
    compute_ph:TrComputePhase action:(Maybe ^TrActionPhase)
    aborted:Bool destroyed:Bool = TransactionDescr;
//
split_merge_info$_ cur_shard_pfx_len:(## 6)
    acc_split_depth:(## 6) this_addr:bits256 sibling_addr:bits256
    = SplitMergeInfo;
trans_split_prepare$0100 split_info:SplitMergeInfo
    storage_ph:(Maybe TrStoragePhase)
    compute_ph:TrComputePhase action:(Maybe ^TrActionPhase)
    aborted:Bool destroyed:Bool
    = TransactionDescr;
trans_split_install$0101 split_info:SplitMergeInfo
    prepare_transaction:^Transaction
    installed:Bool = TransactionDescr;

trans_merge_prepare$0110 split_info:SplitMergeInfo
    storage_ph:TrStoragePhase aborted:Bool
    = TransactionDescr;
trans_merge_install$0111 split_info:SplitMergeInfo
    prepare_transaction:^Transaction
    storage_ph:(Maybe TrStoragePhase)
    credit_ph:(Maybe TrCreditPhase)
    compute_ph:TrComputePhase action:(Maybe ^TrActionPhase)
    aborted:Bool destroyed:Bool
    = TransactionDescr;
'''

@dataclass(frozen=True, slots=True)
class TransactionOrdinary(TlbConstructor):
    '''
    trans_ord$0000 credit_first:Bool
        storage_ph:(Maybe TrStoragePhase)
        credit_ph:(Maybe TrCreditPhase)
        compute_ph:TrComputePhase action:(Maybe ^TrActionPhase)
        aborted:Bool bounce:(Maybe TrBouncePhase)
        destroyed:Bool
        = TransactionDescr;
    '''
    credit_first: bool
    storage_ph: TrStoragePhase | None
    credit_ph: TrCreditPhase | None
    compute_ph: TrComputePhase
    action: TrActionPhase | None
    aborted: bool
    bounce: TrBouncePhase | None
    destroyed: bool

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return 0b0000, 4

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        credit_first: bool = s.load_bool()
        storage_ph: TrStoragePhase | None = s.load_maybe_tlb(TrStoragePhase)
        credit_ph: TrCreditPhase | None = s.load_maybe_tlb(TrCreditPhase)
        compute_ph: TrComputePhase = s.load_tlb(tr_compute_phase)
        action: TrActionPhase | None = s.load_maybe_ref_tlb(TrActionPhase)
        aborted: bool = s.load_bool()
        bounce: TrBouncePhase | None = s.load_maybe_tlb(tr_bounce_phase)
        destroyed: bool = s.load_bool()
        return cls(credit_first, storage_ph, credit_ph,
                   compute_ph, action, aborted, bounce, destroyed)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_bool(self.credit_first)
        b.store_maybe_tlb(self.storage_ph)
        b.store_maybe_tlb(self.credit_ph)
        b.store_tlb(self.compute_ph)
        b.store_maybe_ref_tlb(self.action)
        b.store_bool(self.aborted)
        b.store_maybe_tlb(self.bounce)
        b.store_bool(self.destroyed)
        return b

@dataclass(frozen=True, slots=True)
class TransactionStorage(TlbConstructor):
    '''
    trans_storage$0001 storage_ph:TrStoragePhase
        = TransactionDescr;
    '''
    storage_ph: TrStoragePhase

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return 0b0001, 4

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        storage_ph = s.load_tlb(TrStoragePhase)
        return cls(storage_ph)

    def serialize_fields(self, b: Builder) -> Builder:
        return b.store_tlb(self.storage_ph)

@dataclass(frozen=True, slots=True)
class TransactionTickTock(TlbConstructor):
    '''
    trans_tick_tock$001 is_tock:Bool storage_ph:TrStoragePhase
        compute_ph:TrComputePhase action:(Maybe ^TrActionPhase)
        aborted:Bool destroyed:Bool = TransactionDescr;
    '''
    is_tock: bool
    storage_ph: TrStoragePhase
    compute_ph: TrComputePhase
    action: TrActionPhase | None
    aborted: bool
    destroyed: bool

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return 0b001, 3

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        is_tock = s.load_bool()
        storage_ph = s.load_tlb(TrStoragePhase)
        compute_ph = s.load_tlb(tr_compute_phase)
        action = s.load_maybe_ref_tlb(TrActionPhase)
        aborted = s.load_bool()
        destroyed = s.load_bool()
        return cls(is_tock, storage_ph, compute_ph,
                   action, aborted, destroyed)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_bool(self.is_tock)
        b.store_tlb(self.storage_ph)
        b.store_tlb(self.compute_ph)
        b.store_maybe_ref_tlb(self.action)
        b.store_bool(self.aborted)
        b.store_bool(self.destroyed)
        return b

@dataclass(frozen=True, slots=True)
class TransactionSplitPrepare(TlbConstructor):
    '''
    trans_split_prepare$0100 split_info:SplitMergeInfo
        storage_ph:(Maybe TrStoragePhase)
        compute_ph:TrComputePhase action:(Maybe ^TrActionPhase)
        aborted:Bool destroyed:Bool
        = TransactionDescr;
    '''

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        raise NotImplementedError

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        raise NotImplementedError

    def serialize_fields(self, b: Builder) -> Builder:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class TransactionSplitInstall(TlbConstructor):
    '''
    trans_split_install$0101 split_info:SplitMergeInfo
        prepare_transaction:^Transaction
        installed:Bool = TransactionDescr;
    '''

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        raise NotImplementedError

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        raise NotImplementedError

    def serialize_fields(self, b: Builder) -> Builder:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class TransactionMergePrepare(TlbConstructor):
    '''
    trans_merge_prepare$0110 split_info:SplitMergeInfo
        storage_ph:TrStoragePhase aborted:Bool
        = TransactionDescr;
    '''

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        raise NotImplementedError

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        raise NotImplementedError

    def serialize_fields(self, b: Builder) -> Builder:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class TransactionMergeInstall(TlbConstructor):
    '''
    trans_merge_install$0111 split_info:SplitMergeInfo
        prepare_transaction:^Transaction
        storage_ph:(Maybe TrStoragePhase)
        credit_ph:(Maybe TrCreditPhase)
        compute_ph:TrComputePhase action:(Maybe ^TrActionPhase)
        aborted:Bool destroyed:Bool
        = TransactionDescr;
    '''

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        raise NotImplementedError

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        raise NotImplementedError

    def serialize_fields(self, b: Builder) -> Builder:
        raise NotImplementedError


TransactionDescr = (
    TransactionOrdinary 
    | TransactionStorage
    | TransactionTickTock
    | TransactionSplitPrepare
    | TransactionSplitInstall
    | TransactionMergePrepare
    | TransactionMergeInstall
)

def transaction_descr(s: Slice) -> TransactionDescr:
    tag = s.preload_uint(4)
    match tag:
        case 0b0000: return TransactionOrdinary.deserialize(s)
        case 0b0001: return TransactionStorage.deserialize(s)
        case 0b0010: return TransactionTickTock.deserialize(s)
        case 0b0011: return TransactionTickTock.deserialize(s)
        case _: raise NotImplementedError
