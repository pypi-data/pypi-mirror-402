from dataclasses import dataclass
from typing import Self

from agton.ton import Cell, Slice, Builder, TlbConstructor

from ..types import PoolParams

@dataclass(frozen=True, slots=True)
class DepositLiquidityPayload(TlbConstructor):
    '''
    deposit_liquidity#40e108d6 pool_params:PoolParams min_lp_amount:Coins
                           asset0_target_balance:Coins asset1_target_balance:Coins
                           fulfill_payload:(Maybe ^Cell)
                           reject_payload:(Maybe ^Cell) = ForwardPayload;
    '''
    pool_params: PoolParams
    min_lp_amount: int
    asset0_target_balance: int
    asset1_target_balance: int
    fulfill_payload: Cell | None
    reject_payload: Cell | None

    @classmethod
    def tag(cls):
        return 0x40e108d6, 32
    
    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        pool_params = s.load_tlb(PoolParams)
        min_lp_amount = s.load_coins()
        asset0_target_balance = s.load_coins()
        asset1_target_balance = s.load_coins()
        fulfill_payload = s.load_maybe_ref()
        reject_payload = s.load_maybe_ref()
        return cls(pool_params, min_lp_amount,
                   asset0_target_balance, asset1_target_balance,
                   fulfill_payload, reject_payload)
    
    def serialize_fields(self, b: Builder) -> Builder:
        return (
            b
            .store_tlb(self.pool_params)
            .store_coins(self.min_lp_amount)
            .store_coins(self.asset0_target_balance)
            .store_coins(self.asset1_target_balance)
            .store_maybe_ref(self.fulfill_payload)
            .store_maybe_ref(self.reject_payload)
        )
