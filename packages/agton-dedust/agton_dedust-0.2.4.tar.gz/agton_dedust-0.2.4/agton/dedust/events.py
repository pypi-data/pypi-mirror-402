from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from agton.ton import Slice, Builder, MsgAddressInt, MsgAddress, begin_cell
from agton.ton import TlbConstructor
from .types.asset import Asset, asset


@dataclass(frozen=True, slots=True)
class Swap(TlbConstructor):
    '''
    swap#9c610de3 asset_in:Asset asset_out:Asset amount_in:Coins amount_out:Coins
                  ^[ sender_addr:MsgAddressInt referral_addr:MsgAddress
                  reserve0:Coins reserve1:Coins ] = ExtOutMsgBody;
    '''
    asset_in: Asset
    asset_out: Asset
    amount_in: int
    amount_out: int
    sender_addr: MsgAddressInt
    referral_addr: MsgAddress
    reserve0: int
    reserve1: int

    @classmethod
    def tag(cls):
        return 0x9c610de3, 32

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Swap:
        asset_in = s.load_tlb(asset)
        asset_out = s.load_tlb(asset)
        amount_in = s.load_coins()
        amount_out = s.load_coins()
        s = s.load_ref().begin_parse()
        sender_addr = s.load_msg_address_int()
        referral_addr = s.load_msg_address()
        reserve0 = s.load_coins()
        reserve1 = s.load_coins()
        return cls(
            asset_in, asset_out, amount_in, amount_out,
            sender_addr, referral_addr, reserve0, reserve1
        )

    def serialize_fields(self, b: Builder) -> Builder:
        return (
            b
            .store_tlb(self.asset_in)
            .store_tlb(self.asset_out)
            .store_coins(self.amount_in)
            .store_coins(self.amount_out)
            .store_ref(
                begin_cell()
                .store_msg_address_int(self.sender_addr)
                .store_msg_address(self.referral_addr)
                .store_coins(self.reserve0)
                .store_coins(self.reserve1)
                .end_cell()
            )
        )


@dataclass(frozen=True, slots=True)
class Deposit(TlbConstructor):
    '''
    deposit#b544f4a4 sender_addr:MsgAddressInt amount0:Coins amount1:Coins
                     reserve0:Coins reserve1:Coins liquidity:Coins = ExtOutMsgBody;
    '''
    sender_addr: MsgAddressInt
    amount0: int
    amount1: int
    reserve0: int
    reserve1: int
    liquidity: int

    @classmethod
    def tag(cls):
        return 0xb544f4a4, 32

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        sender_addr = s.load_msg_address_int()
        amount0 = s.load_coins()
        amount1 = s.load_coins()
        reserve0 = s.load_coins()
        reserve1 = s.load_coins()
        liquidity = s.load_coins()
        return cls(sender_addr, amount0, amount1, reserve0, reserve1, liquidity)

    def serialize_fields(self, b: Builder) -> Builder:
        return (
            b
            .store_msg_address_int(self.sender_addr)
            .store_coins(self.amount0)
            .store_coins(self.amount1)
            .store_coins(self.reserve0)
            .store_coins(self.reserve1)
            .store_coins(self.liquidity) 
        )


@dataclass(frozen=True)
class Withdrawal(TlbConstructor):
    '''
    withdrawal#3aa870a6 sender_addr:MsgAddressInt liquidity:Coins
                        amount0:Coins amount1:Coins
                        reserve0:Coins reserve1:Coins = ExtOutMsgBody;
    '''
    sender_addr: MsgAddressInt
    liquidity: int
    amount0: int
    amount1: int
    reserve0: int
    reserve1: int

    @classmethod
    def tag(cls):
        return 0x3aa870a6, 32

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        sender_addr = s.load_msg_address_int()
        liquidity = s.load_coins()
        amount0 = s.load_coins()
        amount1 = s.load_coins()
        reserve0 = s.load_coins()
        reserve1 = s.load_coins()
        return cls(sender_addr, liquidity, amount0, amount1, reserve0, reserve1)

    def serialize_fields(self, b: Builder) -> Builder:
        return (
            b
            .store_msg_address_int(self.sender_addr)
            .store_coins(self.liquidity)
            .store_coins(self.amount0)
            .store_coins(self.amount1)
            .store_coins(self.reserve0)
            .store_coins(self.reserve1)
        )


Event = Swap | Deposit | Withdrawal

def event(s: Slice) -> Event:
    tag = s.preload_uint(32)
    if tag == Swap.tag()[0]:
        return Swap.deserialize(s)
    elif tag == Deposit.tag()[0]:
        return Deposit.deserialize(s)
    elif tag == Withdrawal.tag()[0]:
        return Withdrawal.deserialize(s)
    else:
        raise ValueError(f"Unknown dedust event tag: {tag:08x}")
