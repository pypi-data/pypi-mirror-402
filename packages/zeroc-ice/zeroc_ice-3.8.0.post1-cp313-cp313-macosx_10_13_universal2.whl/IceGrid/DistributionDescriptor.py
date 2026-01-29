# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.StringSeq import _Ice_StringSeq_t

from dataclasses import dataclass
from dataclasses import field


@dataclass
class DistributionDescriptor:
    """
    Describes a distribution.
    
    Attributes
    ----------
    icepatch : str
        The proxy of the IcePatch2 server.
    directories : list[str]
        The source directories.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::DistributionDescriptor``.
    """
    icepatch: str = ""
    directories: list[str] = field(default_factory=list)

_IceGrid_DistributionDescriptor_t = IcePy.defineStruct(
    "::IceGrid::DistributionDescriptor",
    DistributionDescriptor,
    (),
    (
        ("icepatch", (), IcePy._t_string),
        ("directories", (), _Ice_StringSeq_t)
    ))

__all__ = ["DistributionDescriptor", "_IceGrid_DistributionDescriptor_t"]
