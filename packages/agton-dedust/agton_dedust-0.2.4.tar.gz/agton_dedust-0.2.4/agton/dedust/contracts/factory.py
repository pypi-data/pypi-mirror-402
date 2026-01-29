from __future__ import annotations

from typing import overload

from agton.ton import Contract, Provider, Address, MsgAddressInt, Slice, Cell

from ..types import SwapStep
from ..types import SwapStepParams
from ..types import SwapKind, GivenIn
from ..types import Asset, ExtraCurrency, Jetton, Native
from ..types import PoolType, Volatile

from .jetton_vault import JettonVault
from .native_vault import NativeVault
from .pool import Pool


class Factory(Contract):
    @classmethod
    def from_mainnet(cls, provider: Provider) -> Factory:
        a = Address.parse('EQBfBWT7X2BHg9tXAxzhz2aKiNTU1tpt5NsiK0uSDW_YAJ67')
        return cls(provider, a)

    def get_vault_address(self, asset: Asset) -> MsgAddressInt:
        s = self.run_get_method('get_vault_address', [asset.to_slice()])
        match s:
            case Slice():
                return s.load_msg_address_int()
            case Cell():
                return s.begin_parse().load_msg_address_int()
            case _:
                raise TypeError(f'Unexpected result for get_vault_address: {s!r}')

    @overload
    def get_vault(self, asset: Native) -> NativeVault: ...

    @overload
    def get_vault(self, asset: Jetton) -> JettonVault: ...
    
    def get_vault(self, asset: Asset) -> NativeVault | JettonVault:
        address = self.get_vault_address(asset)
        match asset:
            case Native(): 
                return NativeVault(self.provider, address)
            case Jetton():
                return JettonVault(self.provider, address)
            case ExtraCurrency():
                raise NotImplementedError('Not implemented by DeDust itself')
    
    def get_pool_address(self,
                         asset0: Asset,
                         asset1: Asset,
                         pool_type: PoolType | int = Volatile()) -> MsgAddressInt:
        if isinstance(pool_type, PoolType):
            pool_type = 0 if isinstance(pool_type, Volatile) else 1
        s = self.run_get_method('get_pool_address', [pool_type, asset0.to_slice(), asset1.to_slice()])

        match s:
            case Slice():
                return s.load_msg_address_int()
            case Cell():
                return s.begin_parse().load_msg_address_int()
            case _:
                raise TypeError(f'Unexpected result for get_pool_address: {s!r}')
    
    def get_pool(self,
                 asset0: Asset,
                 asset1: Asset,
                 pool_type: PoolType | int = Volatile()) -> Pool:
        a = self.get_pool_address(asset0, asset1, pool_type)
        return Pool(self.provider, a)
