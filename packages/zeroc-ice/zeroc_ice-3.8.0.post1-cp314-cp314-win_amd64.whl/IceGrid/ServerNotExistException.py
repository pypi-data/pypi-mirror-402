# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class ServerNotExistException(UserException):
    """
    The exception that is thrown when IceGrid does not know a server with the provided server ID.
    
    Attributes
    ----------
    id : str
        The server ID.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceGrid::ServerNotExistException``.
    """
    id: str = ""

    _ice_id = "::IceGrid::ServerNotExistException"

_IceGrid_ServerNotExistException_t = IcePy.defineException(
    "::IceGrid::ServerNotExistException",
    ServerNotExistException,
    (),
    None,
    (("id", (), IcePy._t_string, False, 0),))

setattr(ServerNotExistException, '_ice_type', _IceGrid_ServerNotExistException_t)

__all__ = ["ServerNotExistException", "_IceGrid_ServerNotExistException_t"]
