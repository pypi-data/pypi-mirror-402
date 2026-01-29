# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class ServerStartException(UserException):
    """
    The exception that is thrown when a server failed to start.
    
    Attributes
    ----------
    id : str
        The server ID.
    reason : str
        The reason for the failure.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceGrid::ServerStartException``.
    """
    id: str = ""
    reason: str = ""

    _ice_id = "::IceGrid::ServerStartException"

_IceGrid_ServerStartException_t = IcePy.defineException(
    "::IceGrid::ServerStartException",
    ServerStartException,
    (),
    None,
    (
        ("id", (), IcePy._t_string, False, 0),
        ("reason", (), IcePy._t_string, False, 0)
    ))

setattr(ServerStartException, '_ice_type', _IceGrid_ServerStartException_t)

__all__ = ["ServerStartException", "_IceGrid_ServerStartException_t"]
