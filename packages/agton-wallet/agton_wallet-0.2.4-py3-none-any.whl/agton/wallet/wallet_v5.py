from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from agton.ton import Cell, Slice, MsgAddressInt, begin_cell
from agton.ton import Contract, HashmapCodec
from agton.ton.types import OutAction, ActionSendMsg, out_action
from agton.ton.types import OutList, out_list
from agton.ton.types.tlb import TlbConstructor, TlbDeserializationError
from agton.ton.cell.builder import Builder


@dataclass(frozen=True, slots=True)
class AddExtension(TlbConstructor):
    '''add_extension#02 addr:MsgAddressInt = W5ExtendedAction;'''
    addr: MsgAddressInt

    @classmethod
    def tag(cls):
        return 0x02, 8

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        addr = s.load_msg_address_int()
        return cls(addr)

    def serialize_fields(self, b: Builder) -> Builder:
        return b.store_msg_address_int(self.addr)


@dataclass(frozen=True, slots=True)
class DeleteExtension(TlbConstructor):
    '''delete_extension#03 addr:MsgAddressInt = W5ExtendedAction;'''
    addr: MsgAddressInt

    @classmethod
    def tag(cls):
        return 0x03, 8

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        addr = s.load_msg_address_int()
        return cls(addr)

    def serialize_fields(self, b: Builder) -> Builder:
        return b.store_msg_address_int(self.addr)


@dataclass(frozen=True, slots=True)
class SetSignatureAuthAllowed(TlbConstructor):
    '''set_signature_auth_allowed#04 allowed:Bool = W5ExtendedAction;'''
    allowed: bool

    @classmethod
    def tag(cls):
        return 0x04, 8

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        allowed = s.load_bool()
        return cls(allowed)

    def serialize_fields(self, b: Builder) -> Builder:
        return b.store_bool(self.allowed)

W5ExtendedAction = AddExtension | DeleteExtension | SetSignatureAuthAllowed

def w5_extended_action(s: Slice) -> W5ExtendedAction:
    tag = s.preload_uint(8)
    if tag == AddExtension.tag()[0]:
        return AddExtension.deserialize(s)
    if tag == DeleteExtension.tag()[0]:
        return DeleteExtension.deserialize(s)
    if tag == SetSignatureAuthAllowed.tag()[0]:
        return SetSignatureAuthAllowed.deserialize(s)
    raise TlbDeserializationError(f'Unknown tag for ExtendedAction: {tag:08x}')


@dataclass(frozen=True, slots=True)
class ExtendedListLast(TlbConstructor):
    '''extended_list_last$_ action:W5ExtendedAction = W5ExtendedActionList 0;'''
    action: W5ExtendedAction

    @classmethod
    def tag(cls):
        return None

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        action = s.load_tlb(w5_extended_action)
        return cls(action)

    def serialize_fields(self, b: Builder) -> Builder:
        return b.store_tlb(self.action)

@dataclass(frozen=True, slots=True)
class ExtendedListCons(TlbConstructor):
    '''extended_list_action$_ {m:#} action:W5ExtendedAction prev:^(W5ExtendedActionList m) = W5ExtendedActionList (m + 1);'''
    action: W5ExtendedAction
    prev: W5ExtendedActionList

    @classmethod
    def tag(cls):
        return None

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        action = s.load_tlb(w5_extended_action)
        prev = s.load_ref_tlb(w5_extended_action_list)
        return cls(action, prev)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_tlb(self.action)
        b.store_ref_tlb(self.prev)
        return b

W5ExtendedActionList = ExtendedListLast | ExtendedListCons

def w5_extended_action_list(s: Slice) -> W5ExtendedActionList:
    '''
    This is incorrect implementation
    will work as long as after W5ExtendedList in cell there are no possible refs
    '''
    if s.remaining_refs == 0:
        return ExtendedListLast.deserialize(s)
    return ExtendedListCons.deserialize(s)

@dataclass(frozen=True, slots=True)
class W5InnerRequest(TlbConstructor):
    '''
    w5_actions_request$_ {m:#} {n:#} 
        out_actions:(Maybe ^(OutList m)) 
        extended_actions:(Maybe (W5ExtendedActionList n)) 
        = W5InnerRequest m n;
    '''
    out_actions: OutList | None
    extended_actions: W5ExtendedActionList | None

    @classmethod
    def tag(cls):
        return None

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        out_actions = s.load_maybe_ref_tlb(out_list)
        extended_actions = s.load_maybe_tlb(w5_extended_action_list)
        return cls(out_actions, extended_actions)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_maybe_ref_tlb(self.out_actions)
        b.store_maybe_tlb(self.extended_actions)
        return b

@dataclass(frozen=True, slots=True)
class W5SignedRequest(TlbConstructor):
    '''
    w5_signed_request$_ {m:#} {n:#}
        wallet_id:    uint32
        valid_until:  uint32
        msg_seqno:    uint32
        inner:        (W5InnerRequest m n)
        signature:    bits512
    = W5SignedRequest m n;
    '''
    wallet_id: int
    valid_until: int
    msg_seqno: int
    inner: W5InnerRequest
    signature: bytes

    @classmethod
    def tag(cls):
        return None

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        wallet_id = s.load_uint(32)
        valid_until = s.load_uint(32)
        msg_seqno = s.load_uint(32)
        inner = s.load_tlb(W5InnerRequest)
        signature = s.load_bytes(64)
        return cls(wallet_id, valid_until, msg_seqno, inner, signature)

    def serialize_fields(self, b: Builder) -> Builder:
        raise NotImplementedError

    def __post_init__(self):
        if len(self.signature) != 64:
            raise ValueError(f'Expected 64 bytes in signature, but {len(self.signature)} found')

@dataclass(frozen=True, slots=True)
class W5InternalSignedRequest(TlbConstructor):
    '''w5_internal_signed_request#73696e74 {m:#} {n:#} request:(W5SignedRequest m n) = W5MsgBody m n;'''
    request: W5SignedRequest

    @classmethod
    def tag(cls):
        return 0x73696e74, 32

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        request = s.load_tlb(W5SignedRequest)
        return cls(request)

    def serialize_fields(self, b: Builder) -> Builder:
        return b.store_tlb(self.request)

@dataclass(frozen=True, slots=True)
class W5ExternalSignedRequest(TlbConstructor):
    '''w5_external_signed_request#7369676e {m:#} {n:#} request:(W5SignedRequest m n) = W5MsgBody m n;'''
    request: W5SignedRequest

    @classmethod
    def tag(cls):
        return 0x7369676e, 32

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        request = s.load_tlb(W5SignedRequest)
        return cls(request)

    def serialize_fields(self, b: Builder) -> Builder:
        return b.store_tlb(self.request)

@dataclass(frozen=True, slots=True)
class W5ExtensionActionRequest(TlbConstructor):
    '''
    w5_extension_action_request#6578746e {m:#} {n:#}
        query_id:uint64 
        request:(W5InnerRequest m n) 
    = W5MsgBody m n;
    '''
    query_id: int
    request: W5InnerRequest

    @classmethod
    def tag(cls):
        return 0x6578746e, 32

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        query_id = s.load_uint(64)
        request = s.load_tlb(W5InnerRequest)
        return cls(query_id, request)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_uint(self.query_id, 64)
        b.store_tlb(self.request)
        return b

W5MsgBody = W5InternalSignedRequest | W5ExternalSignedRequest | W5ExtensionActionRequest

def w5_msg_body(s: Slice) -> W5MsgBody:
    tag = s.load_uint(64)
    if tag == W5InternalSignedRequest.tag()[0]:
        return W5InternalSignedRequest.deserialize(s)
    if tag == W5ExternalSignedRequest.tag()[0]:
        return W5ExternalSignedRequest.deserialize(s)
    if tag == W5ExtensionActionRequest.tag()[0]:
        return W5ExtensionActionRequest.deserialize(s)
    raise TlbDeserializationError(f'Unexpected tag for W5MsgBody: {tag:08x}')


@dataclass(frozen=True, slots=True)
class WalletV5Data(TlbConstructor):
    '''
    contract_state$_ 
        is_signature_allowed: bool
        seqno:                uint32
        wallet_id:            uint32
        public_key:           bits256
        extensions_dict:      (HashmapE 256 bool)
    = ContractState;
    '''
    is_signature_allowed: bool
    seqno: int
    wallet_id: int
    public_key: bytes
    extensions_dict: dict[bytes, bool]

    @classmethod
    def tag(cls):
        return None

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        is_signature_allowed = s.load_bool()
        seqno = s.load_uint(32)
        wallet_id = s.load_uint(32)
        public_key = s.load_bytes(32)
        extensions_codec = HashmapCodec().with_bytes_keys(32).with_bool_values()
        extensions_hashmap_e = s.load_hashmap_e(256)
        extensions_dict = extensions_codec.decode(extensions_hashmap_e)
        return cls(is_signature_allowed, seqno, wallet_id, public_key, extensions_dict)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_bool(self.is_signature_allowed)
        b.store_uint(self.seqno, 32)
        b.store_uint(self.wallet_id, 32)
        b.store_bytes(self.public_key)
        extensions_codec = HashmapCodec().with_bytes_keys(32).with_bool_values()
        extensions_hashmap_e = extensions_codec.encode(self.extensions_dict)
        b.store_hashmap_e(extensions_hashmap_e, 256)
        return b
    
    @classmethod
    def initial(cls,
                public_key: bytes,
                wallet_id: int,
                is_signature_allowed: bool = True,
                extensions_dict: dict[bytes, bool] | None = None) -> WalletV5Data:
        if extensions_dict is None:
            extensions_dict = dict()
        return cls(
            is_signature_allowed=is_signature_allowed,
            seqno=0,
            wallet_id=wallet_id,
            public_key=public_key,
            extensions_dict=extensions_dict
        )

    def __post_init__(self):
        if len(self.public_key) != 32:
            raise ValueError(f'Expected 32 bytes in public_key, but {len(self.public_key)} found')
