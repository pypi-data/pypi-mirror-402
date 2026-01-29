# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.LoadBalancingPolicy_forward import _IceGrid_LoadBalancingPolicy_t

from IceGrid.ObjectDescriptorSeq import _IceGrid_ObjectDescriptorSeq_t

from dataclasses import dataclass
from dataclasses import field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IceGrid.LoadBalancingPolicy import LoadBalancingPolicy
    from IceGrid.ObjectDescriptor import ObjectDescriptor


@dataclass
class ReplicaGroupDescriptor:
    """
    Describes a replica group.
    
    Attributes
    ----------
    id : str
        The replica group ID.
    loadBalancing : LoadBalancingPolicy | None
        The load balancing policy.
    proxyOptions : str
        Default options for proxies created for the replica group.
    objects : list[ObjectDescriptor]
        The descriptors for the well-known objects.
    description : str
        The description of this replica group.
    filter : str
        The filter to use for this replica group.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::ReplicaGroupDescriptor``.
    """
    id: str = ""
    loadBalancing: LoadBalancingPolicy | None = None
    proxyOptions: str = ""
    objects: list[ObjectDescriptor] = field(default_factory=list)
    description: str = ""
    filter: str = ""

_IceGrid_ReplicaGroupDescriptor_t = IcePy.defineStruct(
    "::IceGrid::ReplicaGroupDescriptor",
    ReplicaGroupDescriptor,
    (),
    (
        ("id", (), IcePy._t_string),
        ("loadBalancing", (), _IceGrid_LoadBalancingPolicy_t),
        ("proxyOptions", (), IcePy._t_string),
        ("objects", (), _IceGrid_ObjectDescriptorSeq_t),
        ("description", (), IcePy._t_string),
        ("filter", (), IcePy._t_string)
    ))

__all__ = ["ReplicaGroupDescriptor", "_IceGrid_ReplicaGroupDescriptor_t"]
