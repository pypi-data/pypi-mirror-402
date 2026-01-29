# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class AdapterNotFoundException(UserException):
    """
    The exception that is thrown by a :class:`Ice.LocatorPrx` implementation when it cannot find an object adapter with the
    provided adapter ID.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::Ice::AdapterNotFoundException``.
    """

    _ice_id = "::Ice::AdapterNotFoundException"

_Ice_AdapterNotFoundException_t = IcePy.defineException(
    "::Ice::AdapterNotFoundException",
    AdapterNotFoundException,
    (),
    None,
    ())

setattr(AdapterNotFoundException, '_ice_type', _Ice_AdapterNotFoundException_t)

__all__ = ["AdapterNotFoundException", "_Ice_AdapterNotFoundException_t"]
