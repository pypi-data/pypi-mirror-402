# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class SessionNotExistException(UserException):
    """
    The exception that is thrown when a client tries to destroy a session with a router, but no session exists for
    this client.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::Glacier2::SessionNotExistException``.
    
    See Also
    --------
        :meth:`Glacier2.RouterPrx.destroySessionAsync`
    """

    _ice_id = "::Glacier2::SessionNotExistException"

_Glacier2_SessionNotExistException_t = IcePy.defineException(
    "::Glacier2::SessionNotExistException",
    SessionNotExistException,
    (),
    None,
    ())

setattr(SessionNotExistException, '_ice_type', _Glacier2_SessionNotExistException_t)

__all__ = ["SessionNotExistException", "_Glacier2_SessionNotExistException_t"]
