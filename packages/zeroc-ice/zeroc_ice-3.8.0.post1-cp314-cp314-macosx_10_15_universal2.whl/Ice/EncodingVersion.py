# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from dataclasses import dataclass


@dataclass(order=True, unsafe_hash=True)
class EncodingVersion:
    """
    Represents a version of the Slice encoding. Ice supports version 1.0 and 1.1 of this encoding.
    
    Attributes
    ----------
    major : int
        The major version of the Slice encoding.
    minor : int
        The minor version of the Slice encoding.
    
    Notes
    -----
        The Slice encoding is also known as the Ice encoding.
        
        The Slice compiler generated this dataclass from Slice struct ``::Ice::EncodingVersion``.
    """
    major: int = 0
    minor: int = 0

_Ice_EncodingVersion_t = IcePy.defineStruct(
    "::Ice::EncodingVersion",
    EncodingVersion,
    (),
    (
        ("major", (), IcePy._t_byte),
        ("minor", (), IcePy._t_byte)
    ))

__all__ = ["EncodingVersion", "_Ice_EncodingVersion_t"]
