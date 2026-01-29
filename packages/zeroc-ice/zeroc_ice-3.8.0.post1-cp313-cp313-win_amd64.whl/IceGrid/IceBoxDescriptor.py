# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.IceBoxDescriptor_forward import _IceGrid_IceBoxDescriptor_t

from IceGrid.ServerDescriptor import ServerDescriptor

from IceGrid.ServerDescriptor_forward import _IceGrid_ServerDescriptor_t

from IceGrid.ServiceInstanceDescriptorSeq import _IceGrid_ServiceInstanceDescriptorSeq_t

from dataclasses import dataclass
from dataclasses import field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IceGrid.ServiceInstanceDescriptor import ServiceInstanceDescriptor

@dataclass(eq=False)
class IceBoxDescriptor(ServerDescriptor):
    """
    Describes an IceBox server.
    
    Attributes
    ----------
    services : list[ServiceInstanceDescriptor]
        The service instances.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceGrid::IceBoxDescriptor``.
    """
    services: list[ServiceInstanceDescriptor] = field(default_factory=list)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::IceBoxDescriptor"

_IceGrid_IceBoxDescriptor_t = IcePy.defineValue(
    "::IceGrid::IceBoxDescriptor",
    IceBoxDescriptor,
    -1,
    (),
    False,
    _IceGrid_ServerDescriptor_t,
    (("services", (), _IceGrid_ServiceInstanceDescriptorSeq_t, False, 0),))

setattr(IceBoxDescriptor, '_ice_type', _IceGrid_IceBoxDescriptor_t)

__all__ = ["IceBoxDescriptor", "_IceGrid_IceBoxDescriptor_t"]
