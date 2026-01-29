# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.LoadBalancingPolicy import LoadBalancingPolicy

from IceGrid.LoadBalancingPolicy_forward import _IceGrid_LoadBalancingPolicy_t

from IceGrid.RandomLoadBalancingPolicy_forward import _IceGrid_RandomLoadBalancingPolicy_t

from dataclasses import dataclass

@dataclass(eq=False)
class RandomLoadBalancingPolicy(LoadBalancingPolicy):
    """
    The load balancing policy that returns endpoints in a random order.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceGrid::RandomLoadBalancingPolicy``.
    """

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::RandomLoadBalancingPolicy"

_IceGrid_RandomLoadBalancingPolicy_t = IcePy.defineValue(
    "::IceGrid::RandomLoadBalancingPolicy",
    RandomLoadBalancingPolicy,
    -1,
    (),
    False,
    _IceGrid_LoadBalancingPolicy_t,
    ())

setattr(RandomLoadBalancingPolicy, '_ice_type', _IceGrid_RandomLoadBalancingPolicy_t)

__all__ = ["RandomLoadBalancingPolicy", "_IceGrid_RandomLoadBalancingPolicy_t"]
