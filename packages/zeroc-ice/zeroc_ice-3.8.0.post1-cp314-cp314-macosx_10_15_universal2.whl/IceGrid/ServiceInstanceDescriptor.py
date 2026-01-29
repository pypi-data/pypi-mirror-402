# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.PropertySetDescriptor import PropertySetDescriptor
from IceGrid.PropertySetDescriptor import _IceGrid_PropertySetDescriptor_t

from IceGrid.ServiceDescriptor_forward import _IceGrid_ServiceDescriptor_t

from IceGrid.StringStringDict import _IceGrid_StringStringDict_t

from dataclasses import dataclass
from dataclasses import field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IceGrid.ServiceDescriptor import ServiceDescriptor


@dataclass
class ServiceInstanceDescriptor:
    """
    Describes an IceBox service.
    
    Attributes
    ----------
    template : str
        The template used by this instance. It's empty when this instance does not use a template.
    parameterValues : dict[str, str]
        The template parameter values.
    descriptor : ServiceDescriptor | None
        The service definition if the instance isn't a template instance (i.e.: if the template attribute is empty).
    propertySet : PropertySetDescriptor
        The property set.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::ServiceInstanceDescriptor``.
    """
    template: str = ""
    parameterValues: dict[str, str] = field(default_factory=dict)
    descriptor: ServiceDescriptor | None = None
    propertySet: PropertySetDescriptor = field(default_factory=PropertySetDescriptor)

_IceGrid_ServiceInstanceDescriptor_t = IcePy.defineStruct(
    "::IceGrid::ServiceInstanceDescriptor",
    ServiceInstanceDescriptor,
    (),
    (
        ("template", (), IcePy._t_string),
        ("parameterValues", (), _IceGrid_StringStringDict_t),
        ("descriptor", (), _IceGrid_ServiceDescriptor_t),
        ("propertySet", (), _IceGrid_PropertySetDescriptor_t)
    ))

__all__ = ["ServiceInstanceDescriptor", "_IceGrid_ServiceInstanceDescriptor_t"]
