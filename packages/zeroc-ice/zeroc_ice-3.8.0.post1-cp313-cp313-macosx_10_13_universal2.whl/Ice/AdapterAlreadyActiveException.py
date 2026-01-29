# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class AdapterAlreadyActiveException(UserException):
    """
    The exception that is thrown when a server application tries to register endpoints for an object adapter that is
    already active.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::Ice::AdapterAlreadyActiveException``.
    """

    _ice_id = "::Ice::AdapterAlreadyActiveException"

_Ice_AdapterAlreadyActiveException_t = IcePy.defineException(
    "::Ice::AdapterAlreadyActiveException",
    AdapterAlreadyActiveException,
    (),
    None,
    ())

setattr(AdapterAlreadyActiveException, '_ice_type', _Ice_AdapterAlreadyActiveException_t)

__all__ = ["AdapterAlreadyActiveException", "_Ice_AdapterAlreadyActiveException_t"]
