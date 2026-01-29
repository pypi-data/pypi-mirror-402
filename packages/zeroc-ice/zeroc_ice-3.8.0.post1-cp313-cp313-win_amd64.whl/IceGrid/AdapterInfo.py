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
class AdapterInfo:
    """
    Information about an adapter registered with the IceGrid registry.
    
    Attributes
    ----------
    id : str
        The ID of the adapter.
    proxy : ObjectPrx | None
        A dummy direct proxy that contains the adapter endpoints.
    replicaGroupId : str
        The replica group ID of the object adapter, or empty if the adapter doesn't belong to a replica group.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::AdapterInfo``.
    """
    id: str = ""
    proxy: ObjectPrx | None = None
    replicaGroupId: str = ""

_IceGrid_AdapterInfo_t = IcePy.defineStruct(
    "::IceGrid::AdapterInfo",
    AdapterInfo,
    (),
    (
        ("id", (), IcePy._t_string),
        ("proxy", (), _Ice_ObjectPrx_t),
        ("replicaGroupId", (), IcePy._t_string)
    ))

__all__ = ["AdapterInfo", "_IceGrid_AdapterInfo_t"]
