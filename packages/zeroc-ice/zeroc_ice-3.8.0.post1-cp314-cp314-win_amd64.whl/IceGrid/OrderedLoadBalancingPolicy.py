# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.LoadBalancingPolicy import LoadBalancingPolicy

from IceGrid.LoadBalancingPolicy_forward import _IceGrid_LoadBalancingPolicy_t

from IceGrid.OrderedLoadBalancingPolicy_forward import _IceGrid_OrderedLoadBalancingPolicy_t

from dataclasses import dataclass

@dataclass(eq=False)
class OrderedLoadBalancingPolicy(LoadBalancingPolicy):
    """
    The load balancing policy that returns endpoints in order.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceGrid::OrderedLoadBalancingPolicy``.
    """

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::OrderedLoadBalancingPolicy"

_IceGrid_OrderedLoadBalancingPolicy_t = IcePy.defineValue(
    "::IceGrid::OrderedLoadBalancingPolicy",
    OrderedLoadBalancingPolicy,
    -1,
    (),
    False,
    _IceGrid_LoadBalancingPolicy_t,
    ())

setattr(OrderedLoadBalancingPolicy, '_ice_type', _IceGrid_OrderedLoadBalancingPolicy_t)

__all__ = ["OrderedLoadBalancingPolicy", "_IceGrid_OrderedLoadBalancingPolicy_t"]
