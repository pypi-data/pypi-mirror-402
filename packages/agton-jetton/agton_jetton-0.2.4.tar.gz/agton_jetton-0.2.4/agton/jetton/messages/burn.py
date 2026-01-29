from __future__ import annotations
from typing import Self

from agton.ton import MsgAddress, Cell, Builder, Slice, TlbConstructor
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class JettonBurn(TlbConstructor):
    '''
    burn#595f07bc query_id:uint64 amount:(VarUInteger 16)
              response_destination:MsgAddress custom_payload:(Maybe ^Cell)
              = InternalMsgBody;
    '''
    query_id: int
    amount: int
    response_destination: MsgAddress
    custom_payload: Cell | None

    @classmethod
    def tag(cls):
        return 0x595f07bc, 32

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        query_id = s.load_uint(64)
        amount = s.load_coins()
        response_destination = s.load_msg_address()
        custom_payload = s.load_maybe_ref()
        return cls(query_id, amount, response_destination, custom_payload)

    def serialize_fields(self, b: Builder) -> Builder:
        return (
            b
            .store_uint(self.query_id, 64)
            .store_coins(self.amount)
            .store_msg_address(self.response_destination)
            .store_maybe_ref(self.custom_payload)
        )

