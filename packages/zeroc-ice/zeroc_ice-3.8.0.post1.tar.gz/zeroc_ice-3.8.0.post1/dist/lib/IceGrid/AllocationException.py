# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class AllocationException(UserException):
    """
    The exception that is thrown when the allocation of an object failed.
    
    Attributes
    ----------
    reason : str
        The reason why the object couldn't be allocated.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceGrid::AllocationException``.
    """
    reason: str = ""

    _ice_id = "::IceGrid::AllocationException"

_IceGrid_AllocationException_t = IcePy.defineException(
    "::IceGrid::AllocationException",
    AllocationException,
    (),
    None,
    (("reason", (), IcePy._t_string, False, 0),))

setattr(AllocationException, '_ice_type', _IceGrid_AllocationException_t)

__all__ = ["AllocationException", "_IceGrid_AllocationException_t"]
