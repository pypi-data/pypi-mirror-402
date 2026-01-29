# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from dataclasses import dataclass


@dataclass(order=True, unsafe_hash=True)
class PropertyDescriptor:
    """
    Describes an Ice property.
    
    Attributes
    ----------
    name : str
        The name of the property.
    value : str
        The value of the property.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::PropertyDescriptor``.
    """
    name: str = ""
    value: str = ""

_IceGrid_PropertyDescriptor_t = IcePy.defineStruct(
    "::IceGrid::PropertyDescriptor",
    PropertyDescriptor,
    (),
    (
        ("name", (), IcePy._t_string),
        ("value", (), IcePy._t_string)
    ))

__all__ = ["PropertyDescriptor", "_IceGrid_PropertyDescriptor_t"]
