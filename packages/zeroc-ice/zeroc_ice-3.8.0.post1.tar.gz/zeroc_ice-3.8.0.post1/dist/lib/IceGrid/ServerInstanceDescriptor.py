# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.PropertySetDescriptor import PropertySetDescriptor
from IceGrid.PropertySetDescriptor import _IceGrid_PropertySetDescriptor_t

from IceGrid.PropertySetDescriptorDict import _IceGrid_PropertySetDescriptorDict_t

from IceGrid.StringStringDict import _IceGrid_StringStringDict_t

from dataclasses import dataclass
from dataclasses import field

from typing import TYPE_CHECKING


@dataclass
class ServerInstanceDescriptor:
    """
    Describes a template instantiation that creates a server.
    
    Attributes
    ----------
    template : str
        The template used by this instance. It's never empty.
    parameterValues : dict[str, str]
        The template parameter values.
    propertySet : PropertySetDescriptor
        The property set.
    servicePropertySets : dict[str, PropertySetDescriptor]
        The services property sets.
        It's only valid to set these property sets when the template is an IceBox server template.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::ServerInstanceDescriptor``.
    """
    template: str = ""
    parameterValues: dict[str, str] = field(default_factory=dict)
    propertySet: PropertySetDescriptor = field(default_factory=PropertySetDescriptor)
    servicePropertySets: dict[str, PropertySetDescriptor] = field(default_factory=dict)

_IceGrid_ServerInstanceDescriptor_t = IcePy.defineStruct(
    "::IceGrid::ServerInstanceDescriptor",
    ServerInstanceDescriptor,
    (),
    (
        ("template", (), IcePy._t_string),
        ("parameterValues", (), _IceGrid_StringStringDict_t),
        ("propertySet", (), _IceGrid_PropertySetDescriptor_t),
        ("servicePropertySets", (), _IceGrid_PropertySetDescriptorDict_t)
    ))

__all__ = ["ServerInstanceDescriptor", "_IceGrid_ServerInstanceDescriptor_t"]
