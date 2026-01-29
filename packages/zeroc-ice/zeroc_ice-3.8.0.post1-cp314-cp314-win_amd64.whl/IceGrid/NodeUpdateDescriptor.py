# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.StringSeq import _Ice_StringSeq_t

from IceGrid.BoxedString_forward import _IceGrid_BoxedString_t

from IceGrid.PropertySetDescriptorDict import _IceGrid_PropertySetDescriptorDict_t

from IceGrid.ServerDescriptorSeq import _IceGrid_ServerDescriptorSeq_t

from IceGrid.ServerInstanceDescriptorSeq import _IceGrid_ServerInstanceDescriptorSeq_t

from IceGrid.StringStringDict import _IceGrid_StringStringDict_t

from dataclasses import dataclass
from dataclasses import field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IceGrid.BoxedString import BoxedString
    from IceGrid.PropertySetDescriptor import PropertySetDescriptor
    from IceGrid.ServerDescriptor import ServerDescriptor
    from IceGrid.ServerInstanceDescriptor import ServerInstanceDescriptor


@dataclass
class NodeUpdateDescriptor:
    """
    Describes the updates to apply to a node in a deployed application.
    
    Attributes
    ----------
    name : str
        The name of the node to update.
    description : BoxedString | None
        The updated description (or null if the description wasn't updated.)
    variables : dict[str, str]
        The variables to update.
    removeVariables : list[str]
        The variables to remove.
    propertySets : dict[str, PropertySetDescriptor]
        The property sets to update.
    removePropertySets : list[str]
        The property sets to remove.
    serverInstances : list[ServerInstanceDescriptor]
        The server instances to update.
    servers : list[ServerDescriptor | None]
        The servers which are not template instances to update.
    removeServers : list[str]
        The IDs of the servers to remove.
    loadFactor : BoxedString | None
        The updated load factor of the node (or null if the load factor was not updated).
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::NodeUpdateDescriptor``.
    """
    name: str = ""
    description: BoxedString | None = None
    variables: dict[str, str] = field(default_factory=dict)
    removeVariables: list[str] = field(default_factory=list)
    propertySets: dict[str, PropertySetDescriptor] = field(default_factory=dict)
    removePropertySets: list[str] = field(default_factory=list)
    serverInstances: list[ServerInstanceDescriptor] = field(default_factory=list)
    servers: list[ServerDescriptor | None] = field(default_factory=list)
    removeServers: list[str] = field(default_factory=list)
    loadFactor: BoxedString | None = None

_IceGrid_NodeUpdateDescriptor_t = IcePy.defineStruct(
    "::IceGrid::NodeUpdateDescriptor",
    NodeUpdateDescriptor,
    (),
    (
        ("name", (), IcePy._t_string),
        ("description", (), _IceGrid_BoxedString_t),
        ("variables", (), _IceGrid_StringStringDict_t),
        ("removeVariables", (), _Ice_StringSeq_t),
        ("propertySets", (), _IceGrid_PropertySetDescriptorDict_t),
        ("removePropertySets", (), _Ice_StringSeq_t),
        ("serverInstances", (), _IceGrid_ServerInstanceDescriptorSeq_t),
        ("servers", (), _IceGrid_ServerDescriptorSeq_t),
        ("removeServers", (), _Ice_StringSeq_t),
        ("loadFactor", (), _IceGrid_BoxedString_t)
    ))

__all__ = ["NodeUpdateDescriptor", "_IceGrid_NodeUpdateDescriptor_t"]
