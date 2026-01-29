# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.AllocationException import AllocationException
from IceGrid.AllocationException import _IceGrid_AllocationException_t

from dataclasses import dataclass


@dataclass
class AllocationTimeoutException(AllocationException):
    """
    The exception that is thrown when the request to allocate an object times out.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceGrid::AllocationTimeoutException``.
    """

    _ice_id = "::IceGrid::AllocationTimeoutException"

_IceGrid_AllocationTimeoutException_t = IcePy.defineException(
    "::IceGrid::AllocationTimeoutException",
    AllocationTimeoutException,
    (),
    _IceGrid_AllocationException_t,
    ())

setattr(AllocationTimeoutException, '_ice_type', _IceGrid_AllocationTimeoutException_t)

__all__ = ["AllocationTimeoutException", "_IceGrid_AllocationTimeoutException_t"]
