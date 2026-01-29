from dataclasses import dataclass
from typing import Self

from agton.ton import Slice, Builder, TlbConstructor

from ..types import SwapStep, SwapParams

@dataclass(frozen=True, slots=True)
class SwapPayload(TlbConstructor):
    '''swap#e3a0d482 _:SwapStep swap_params:^SwapParams = ForwardPayload;'''
    swap_step: SwapStep
    swap_params: SwapParams

    @classmethod
    def tag(cls):
        return 0xe3a0d482, 32
    
    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        swap_step = s.load_tlb(SwapStep)
        swap_params = s.load_ref_tlb(SwapParams)
        return cls(swap_step, swap_params)
    
    def serialize_fields(self, b: Builder) -> Builder:
        return (
            b
            .store_tlb(self.swap_step)
            .store_ref_tlb(self.swap_params)
        )
