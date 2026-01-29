# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.CommunicatorDescriptor import CommunicatorDescriptor

from IceGrid.CommunicatorDescriptor_forward import _IceGrid_CommunicatorDescriptor_t

from IceGrid.ServiceDescriptor_forward import _IceGrid_ServiceDescriptor_t

from dataclasses import dataclass

@dataclass(eq=False)
class ServiceDescriptor(CommunicatorDescriptor):
    """
    Describes an IceBox service.
    
    Attributes
    ----------
    name : str
        The service name.
    entry : str
        The entry point of the IceBox service.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceGrid::ServiceDescriptor``.
    """
    name: str = ""
    entry: str = ""

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::ServiceDescriptor"

_IceGrid_ServiceDescriptor_t = IcePy.defineValue(
    "::IceGrid::ServiceDescriptor",
    ServiceDescriptor,
    -1,
    (),
    False,
    _IceGrid_CommunicatorDescriptor_t,
    (
        ("name", (), IcePy._t_string, False, 0),
        ("entry", (), IcePy._t_string, False, 0)
    ))

setattr(ServiceDescriptor, '_ice_type', _IceGrid_ServiceDescriptor_t)

__all__ = ["ServiceDescriptor", "_IceGrid_ServiceDescriptor_t"]
