# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.ObjectPrx_forward import _Ice_ObjectPrx_t

from dataclasses import dataclass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Ice.ObjectPrx import ObjectPrx


@dataclass
class ObjectInfo:
    """
    Information about an Ice well-known object.
    
    Attributes
    ----------
    proxy : ObjectPrx | None
        The proxy of the object.
    type : str
        The type of the object.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::ObjectInfo``.
    """
    proxy: ObjectPrx | None = None
    type: str = ""

_IceGrid_ObjectInfo_t = IcePy.defineStruct(
    "::IceGrid::ObjectInfo",
    ObjectInfo,
    (),
    (
        ("proxy", (), _Ice_ObjectPrx_t),
        ("type", (), IcePy._t_string)
    ))

__all__ = ["ObjectInfo", "_IceGrid_ObjectInfo_t"]
