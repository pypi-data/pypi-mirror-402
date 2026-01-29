# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from dataclasses import dataclass


@dataclass(order=True, unsafe_hash=True)
class ProtocolVersion:
    """
    Represents a version of the Ice protocol. The only version implemented and supported by Ice is version 1.0.
    
    Attributes
    ----------
    major : int
        The major version of the Ice protocol.
    minor : int
        The minor version of the Ice protocol.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::Ice::ProtocolVersion``.
    """
    major: int = 0
    minor: int = 0

_Ice_ProtocolVersion_t = IcePy.defineStruct(
    "::Ice::ProtocolVersion",
    ProtocolVersion,
    (),
    (
        ("major", (), IcePy._t_byte),
        ("minor", (), IcePy._t_byte)
    ))

__all__ = ["ProtocolVersion", "_Ice_ProtocolVersion_t"]
