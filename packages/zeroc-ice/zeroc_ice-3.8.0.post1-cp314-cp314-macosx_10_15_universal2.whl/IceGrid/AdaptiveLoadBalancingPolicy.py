# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.AdaptiveLoadBalancingPolicy_forward import _IceGrid_AdaptiveLoadBalancingPolicy_t

from IceGrid.LoadBalancingPolicy import LoadBalancingPolicy

from IceGrid.LoadBalancingPolicy_forward import _IceGrid_LoadBalancingPolicy_t

from dataclasses import dataclass

@dataclass(eq=False)
class AdaptiveLoadBalancingPolicy(LoadBalancingPolicy):
    """
    The load balancing policy that returns the endpoints of the server(s) with the lowest load average.
    
    Attributes
    ----------
    loadSample : str
        The load sample to use for the load balancing. The allowed values for this attribute are "1", "5" and "15",
        representing respectively the load average over the past minute, the past 5 minutes and the past 15 minutes.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceGrid::AdaptiveLoadBalancingPolicy``.
    """
    loadSample: str = ""

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::AdaptiveLoadBalancingPolicy"

_IceGrid_AdaptiveLoadBalancingPolicy_t = IcePy.defineValue(
    "::IceGrid::AdaptiveLoadBalancingPolicy",
    AdaptiveLoadBalancingPolicy,
    -1,
    (),
    False,
    _IceGrid_LoadBalancingPolicy_t,
    (("loadSample", (), IcePy._t_string, False, 0),))

setattr(AdaptiveLoadBalancingPolicy, '_ice_type', _IceGrid_AdaptiveLoadBalancingPolicy_t)

__all__ = ["AdaptiveLoadBalancingPolicy", "_IceGrid_AdaptiveLoadBalancingPolicy_t"]
