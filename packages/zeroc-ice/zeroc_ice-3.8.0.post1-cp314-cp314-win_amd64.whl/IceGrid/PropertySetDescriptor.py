# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.StringSeq import _Ice_StringSeq_t

from IceGrid.PropertyDescriptorSeq import _IceGrid_PropertyDescriptorSeq_t

from dataclasses import dataclass
from dataclasses import field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IceGrid.PropertyDescriptor import PropertyDescriptor


@dataclass
class PropertySetDescriptor:
    """
    A property set descriptor.
    
    Attributes
    ----------
    references : list[str]
        References to named property sets.
    properties : list[PropertyDescriptor]
        The property set properties.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::PropertySetDescriptor``.
    """
    references: list[str] = field(default_factory=list)
    properties: list[PropertyDescriptor] = field(default_factory=list)

_IceGrid_PropertySetDescriptor_t = IcePy.defineStruct(
    "::IceGrid::PropertySetDescriptor",
    PropertySetDescriptor,
    (),
    (
        ("references", (), _Ice_StringSeq_t),
        ("properties", (), _IceGrid_PropertyDescriptorSeq_t)
    ))

__all__ = ["PropertySetDescriptor", "_IceGrid_PropertySetDescriptor_t"]
