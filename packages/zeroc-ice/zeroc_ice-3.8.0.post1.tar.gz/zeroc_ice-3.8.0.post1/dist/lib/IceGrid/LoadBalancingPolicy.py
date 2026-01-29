# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.Value import Value

from IceGrid.LoadBalancingPolicy_forward import _IceGrid_LoadBalancingPolicy_t

from dataclasses import dataclass

@dataclass(eq=False)
class LoadBalancingPolicy(Value):
    """
    The base class for load balancing policies.
    
    Attributes
    ----------
    nReplicas : str
        The number of replicas that will be used to gather the endpoints of a replica group.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceGrid::LoadBalancingPolicy``.
    """
    nReplicas: str = ""

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::LoadBalancingPolicy"

_IceGrid_LoadBalancingPolicy_t = IcePy.defineValue(
    "::IceGrid::LoadBalancingPolicy",
    LoadBalancingPolicy,
    -1,
    (),
    False,
    None,
    (("nReplicas", (), IcePy._t_string, False, 0),))

setattr(LoadBalancingPolicy, '_ice_type', _IceGrid_LoadBalancingPolicy_t)

__all__ = ["LoadBalancingPolicy", "_IceGrid_LoadBalancingPolicy_t"]
