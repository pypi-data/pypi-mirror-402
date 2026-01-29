# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class ServerNotFoundException(UserException):
    """
    The exception that is thrown when a server was not found.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::Ice::ServerNotFoundException``.
    """

    _ice_id = "::Ice::ServerNotFoundException"

_Ice_ServerNotFoundException_t = IcePy.defineException(
    "::Ice::ServerNotFoundException",
    ServerNotFoundException,
    (),
    None,
    ())

setattr(ServerNotFoundException, '_ice_type', _Ice_ServerNotFoundException_t)

__all__ = ["ServerNotFoundException", "_Ice_ServerNotFoundException_t"]
