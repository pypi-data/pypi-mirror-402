# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from dataclasses import dataclass


@dataclass
class LoadInfo:
    """
    Information about the load of a node.
    
    Attributes
    ----------
    avg1 : float
        The load average over the past minute.
    avg5 : float
        The load average over the past 5 minutes.
    avg15 : float
        The load average over the past 15 minutes.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::LoadInfo``.
    """
    avg1: float = 0.0
    avg5: float = 0.0
    avg15: float = 0.0

_IceGrid_LoadInfo_t = IcePy.defineStruct(
    "::IceGrid::LoadInfo",
    LoadInfo,
    (),
    (
        ("avg1", (), IcePy._t_float),
        ("avg5", (), IcePy._t_float),
        ("avg15", (), IcePy._t_float)
    ))

__all__ = ["LoadInfo", "_IceGrid_LoadInfo_t"]
