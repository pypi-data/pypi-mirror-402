# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class ServerStopException(UserException):
    """
    The exception that is thrown when a server failed to stop.
    
    Attributes
    ----------
    id : str
        The server ID.
    reason : str
        The reason for the failure.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceGrid::ServerStopException``.
    """
    id: str = ""
    reason: str = ""

    _ice_id = "::IceGrid::ServerStopException"

_IceGrid_ServerStopException_t = IcePy.defineException(
    "::IceGrid::ServerStopException",
    ServerStopException,
    (),
    None,
    (
        ("id", (), IcePy._t_string, False, 0),
        ("reason", (), IcePy._t_string, False, 0)
    ))

setattr(ServerStopException, '_ice_type', _IceGrid_ServerStopException_t)

__all__ = ["ServerStopException", "_IceGrid_ServerStopException_t"]
