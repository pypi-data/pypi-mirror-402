# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.LoadBalancingPolicy import LoadBalancingPolicy

from IceGrid.LoadBalancingPolicy_forward import _IceGrid_LoadBalancingPolicy_t

from IceGrid.RoundRobinLoadBalancingPolicy_forward import _IceGrid_RoundRobinLoadBalancingPolicy_t

from dataclasses import dataclass

@dataclass(eq=False)
class RoundRobinLoadBalancingPolicy(LoadBalancingPolicy):
    """
    The load balancing policy that returns endpoints using round-robin.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceGrid::RoundRobinLoadBalancingPolicy``.
    """

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::RoundRobinLoadBalancingPolicy"

_IceGrid_RoundRobinLoadBalancingPolicy_t = IcePy.defineValue(
    "::IceGrid::RoundRobinLoadBalancingPolicy",
    RoundRobinLoadBalancingPolicy,
    -1,
    (),
    False,
    _IceGrid_LoadBalancingPolicy_t,
    ())

setattr(RoundRobinLoadBalancingPolicy, '_ice_type', _IceGrid_RoundRobinLoadBalancingPolicy_t)

__all__ = ["RoundRobinLoadBalancingPolicy", "_IceGrid_RoundRobinLoadBalancingPolicy_t"]
