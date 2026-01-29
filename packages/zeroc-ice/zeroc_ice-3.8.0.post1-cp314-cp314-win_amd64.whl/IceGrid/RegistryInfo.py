# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from dataclasses import dataclass


@dataclass(order=True, unsafe_hash=True)
class RegistryInfo:
    """
    Information about an IceGrid registry replica.
    
    Attributes
    ----------
    name : str
        The name of the registry.
    hostname : str
        The network name of the host running this registry.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::RegistryInfo``.
    """
    name: str = ""
    hostname: str = ""

_IceGrid_RegistryInfo_t = IcePy.defineStruct(
    "::IceGrid::RegistryInfo",
    RegistryInfo,
    (),
    (
        ("name", (), IcePy._t_string),
        ("hostname", (), IcePy._t_string)
    ))

__all__ = ["RegistryInfo", "_IceGrid_RegistryInfo_t"]
