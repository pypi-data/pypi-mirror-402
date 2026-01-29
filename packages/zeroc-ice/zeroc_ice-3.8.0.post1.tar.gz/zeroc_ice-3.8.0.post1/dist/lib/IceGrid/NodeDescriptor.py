# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.PropertySetDescriptorDict import _IceGrid_PropertySetDescriptorDict_t

from IceGrid.ServerDescriptorSeq import _IceGrid_ServerDescriptorSeq_t

from IceGrid.ServerInstanceDescriptorSeq import _IceGrid_ServerInstanceDescriptorSeq_t

from IceGrid.StringStringDict import _IceGrid_StringStringDict_t

from dataclasses import dataclass
from dataclasses import field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IceGrid.PropertySetDescriptor import PropertySetDescriptor
    from IceGrid.ServerDescriptor import ServerDescriptor
    from IceGrid.ServerInstanceDescriptor import ServerInstanceDescriptor


@dataclass
class NodeDescriptor:
    """
    Describes an IceGrid node.
    
    Attributes
    ----------
    variables : dict[str, str]
        The variables defined for the node.
    serverInstances : list[ServerInstanceDescriptor]
        The server instances (template instances).
    servers : list[ServerDescriptor | None]
        Servers that are not template instances.
    loadFactor : str
        Load factor of the node.
    description : str
        The description of this node.
    propertySets : dict[str, PropertySetDescriptor]
        Property set descriptors.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::NodeDescriptor``.
    """
    variables: dict[str, str] = field(default_factory=dict)
    serverInstances: list[ServerInstanceDescriptor] = field(default_factory=list)
    servers: list[ServerDescriptor | None] = field(default_factory=list)
    loadFactor: str = ""
    description: str = ""
    propertySets: dict[str, PropertySetDescriptor] = field(default_factory=dict)

_IceGrid_NodeDescriptor_t = IcePy.defineStruct(
    "::IceGrid::NodeDescriptor",
    NodeDescriptor,
    (),
    (
        ("variables", (), _IceGrid_StringStringDict_t),
        ("serverInstances", (), _IceGrid_ServerInstanceDescriptorSeq_t),
        ("servers", (), _IceGrid_ServerDescriptorSeq_t),
        ("loadFactor", (), IcePy._t_string),
        ("description", (), IcePy._t_string),
        ("propertySets", (), _IceGrid_PropertySetDescriptorDict_t)
    ))

__all__ = ["NodeDescriptor", "_IceGrid_NodeDescriptor_t"]
