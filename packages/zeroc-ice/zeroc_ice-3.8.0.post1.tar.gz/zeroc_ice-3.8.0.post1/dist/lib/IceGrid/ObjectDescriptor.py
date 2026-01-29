# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.Identity import Identity
from Ice.Identity import _Ice_Identity_t

from dataclasses import dataclass
from dataclasses import field


@dataclass(order=True, unsafe_hash=True)
class ObjectDescriptor:
    """
    Describes a well-known Ice object.
    
    Attributes
    ----------
    id : Identity
        The identity of the object.
    type : str
        The object type.
    proxyOptions : str
        The proxy options to use when creating a proxy for this well-known object. If empty, the proxy is created
        with the proxy options specified on the object adapter or replica group.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::ObjectDescriptor``.
    """
    id: Identity = field(default_factory=Identity)
    type: str = ""
    proxyOptions: str = ""

_IceGrid_ObjectDescriptor_t = IcePy.defineStruct(
    "::IceGrid::ObjectDescriptor",
    ObjectDescriptor,
    (),
    (
        ("id", (), _Ice_Identity_t),
        ("type", (), IcePy._t_string),
        ("proxyOptions", (), IcePy._t_string)
    ))

__all__ = ["ObjectDescriptor", "_IceGrid_ObjectDescriptor_t"]
