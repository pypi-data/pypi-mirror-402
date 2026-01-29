# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class ObjectNotFoundException(UserException):
    """
    The exception that is thrown by a :class:`Ice.LocatorPrx` implementation when it cannot find an object with the provided
    identity.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::Ice::ObjectNotFoundException``.
    """

    _ice_id = "::Ice::ObjectNotFoundException"

_Ice_ObjectNotFoundException_t = IcePy.defineException(
    "::Ice::ObjectNotFoundException",
    ObjectNotFoundException,
    (),
    None,
    ())

setattr(ObjectNotFoundException, '_ice_type', _Ice_ObjectNotFoundException_t)

__all__ = ["ObjectNotFoundException", "_Ice_ObjectNotFoundException_t"]
