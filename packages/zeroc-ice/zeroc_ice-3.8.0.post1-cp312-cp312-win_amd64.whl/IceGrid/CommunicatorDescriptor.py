# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.StringSeq import _Ice_StringSeq_t

from Ice.Value import Value

from IceGrid.AdapterDescriptorSeq import _IceGrid_AdapterDescriptorSeq_t

from IceGrid.CommunicatorDescriptor_forward import _IceGrid_CommunicatorDescriptor_t

from IceGrid.DbEnvDescriptorSeq import _IceGrid_DbEnvDescriptorSeq_t

from IceGrid.PropertySetDescriptor import PropertySetDescriptor
from IceGrid.PropertySetDescriptor import _IceGrid_PropertySetDescriptor_t

from dataclasses import dataclass
from dataclasses import field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IceGrid.AdapterDescriptor import AdapterDescriptor
    from IceGrid.DbEnvDescriptor import DbEnvDescriptor

@dataclass(eq=False)
class CommunicatorDescriptor(Value):
    """
    Describes an Ice communicator.
    
    Attributes
    ----------
    adapters : list[AdapterDescriptor]
        The indirect object adapters.
    propertySet : PropertySetDescriptor
        The property set.
    dbEnvs : list[DbEnvDescriptor]
        The database environments.
    logs : list[str]
        The path of each log file.
    description : str
        A description of this descriptor.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceGrid::CommunicatorDescriptor``.
    """
    adapters: list[AdapterDescriptor] = field(default_factory=list)
    propertySet: PropertySetDescriptor = field(default_factory=PropertySetDescriptor)
    dbEnvs: list[DbEnvDescriptor] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    description: str = ""

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::CommunicatorDescriptor"

_IceGrid_CommunicatorDescriptor_t = IcePy.defineValue(
    "::IceGrid::CommunicatorDescriptor",
    CommunicatorDescriptor,
    -1,
    (),
    False,
    None,
    (
        ("adapters", (), _IceGrid_AdapterDescriptorSeq_t, False, 0),
        ("propertySet", (), _IceGrid_PropertySetDescriptor_t, False, 0),
        ("dbEnvs", (), _IceGrid_DbEnvDescriptorSeq_t, False, 0),
        ("logs", (), _Ice_StringSeq_t, False, 0),
        ("description", (), IcePy._t_string, False, 0)
    ))

setattr(CommunicatorDescriptor, '_ice_type', _IceGrid_CommunicatorDescriptor_t)

__all__ = ["CommunicatorDescriptor", "_IceGrid_CommunicatorDescriptor_t"]
