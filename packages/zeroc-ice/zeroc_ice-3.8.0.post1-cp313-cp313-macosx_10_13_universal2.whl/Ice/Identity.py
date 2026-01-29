# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from dataclasses import dataclass


@dataclass(order=True, unsafe_hash=True)
class Identity:
    """
    Represents the identity of an Ice object. It is comparable to the path of a URI. Its string representation is
    ``name`` when the category is empty, and ``category/name`` when the category is not empty.
    
    Attributes
    ----------
    name : str
        The name of the Ice object. An empty name is not valid.
    category : str
        The category of the object.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::Ice::Identity``.
    """
    name: str = ""
    category: str = ""

_Ice_Identity_t = IcePy.defineStruct(
    "::Ice::Identity",
    Identity,
    (),
    (
        ("name", (), IcePy._t_string),
        ("category", (), IcePy._t_string)
    ))

__all__ = ["Identity", "_Ice_Identity_t"]
