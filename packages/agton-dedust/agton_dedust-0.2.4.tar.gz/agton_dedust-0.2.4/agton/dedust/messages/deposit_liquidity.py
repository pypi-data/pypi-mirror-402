from dataclasses import dataclass
from typing import Self

from agton.dedust.types import PoolParams
from agton.ton import Cell, Slice, Builder, TlbConstructor, begin_cell


@dataclass(frozen=True, slots=True)
class DepositLiquidity(TlbConstructor):
    '''
    deposit_liquidity#d55e4686 query_id:uint64 amount:Coins pool_params:PoolParams
                           ^[ min_lp_amount:Coins
                           asset0_target_balance:Coins asset1_target_balance:Coins ]
                           fulfill_payload:(Maybe ^Cell)
                           reject_payload:(Maybe ^Cell) = InMsgBody;
    '''
    query_id: int
    amount: int
    pool_params: PoolParams
    min_lp_amount: int
    asset0_target_balance: int
    asset1_target_balance: int
    fulfill_payload: Cell | None
    reject_payload: Cell | None

    @classmethod
    def tag(cls):
        return 0xd55e4686, 32

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        query_id = s.load_uint(64)
        amount = s.load_coins()
        pool_params = s.load_tlb(PoolParams)
        deposit = s.load_ref().begin_parse()
        min_lp_amount = deposit.load_coins()
        asset0_target_balance = deposit.load_coins()
        asset1_target_balance = deposit.load_coins()
        fulfill_payload = s.load_maybe_ref()
        reject_payload = s.load_maybe_ref()
        return cls(query_id, amount, pool_params, min_lp_amount,
                   asset0_target_balance, asset1_target_balance,
                   fulfill_payload, reject_payload)

    def serialize_fields(self, b: Builder) -> Builder:
        return (
            b
            .store_uint(self.query_id, 64)
            .store_coins(self.amount)
            .store_tlb(self.pool_params)
            .store_ref(
                begin_cell()
                .store_coins(self.min_lp_amount)
                .store_coins(self.asset0_target_balance)
                .store_coins(self.asset1_target_balance)
                .end_cell()
            )
            .store_maybe_ref(self.fulfill_payload)
            .store_maybe_ref(self.reject_payload)
        )
