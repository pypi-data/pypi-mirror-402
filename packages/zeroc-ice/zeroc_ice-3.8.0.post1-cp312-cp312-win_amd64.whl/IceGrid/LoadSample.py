# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from enum import Enum

class LoadSample(Enum):
    """
    Determines which load sampling interval to use.
    
    Notes
    -----
        The Slice compiler generated this enum class from Slice enumeration ``::IceGrid::LoadSample``.
    """

    LoadSample1 = 0
    """
    Sample every minute.
    """

    LoadSample5 = 1
    """
    Sample every five minutes.
    """

    LoadSample15 = 2
    """
    Sample every fifteen minutes.
    """

_IceGrid_LoadSample_t = IcePy.defineEnum(
    "::IceGrid::LoadSample",
    LoadSample,
    (),
    {
        0: LoadSample.LoadSample1,
        1: LoadSample.LoadSample5,
        2: LoadSample.LoadSample15,
    }
)

__all__ = ["LoadSample", "_IceGrid_LoadSample_t"]
