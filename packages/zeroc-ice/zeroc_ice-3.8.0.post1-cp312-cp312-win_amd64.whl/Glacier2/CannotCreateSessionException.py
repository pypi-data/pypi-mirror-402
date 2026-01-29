# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class CannotCreateSessionException(UserException):
    """
    The exception that is thrown when an attempt to create a new session fails.
    
    Attributes
    ----------
    reason : str
        The reason why the session creation failed.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::Glacier2::CannotCreateSessionException``.
    """
    reason: str = ""

    _ice_id = "::Glacier2::CannotCreateSessionException"

_Glacier2_CannotCreateSessionException_t = IcePy.defineException(
    "::Glacier2::CannotCreateSessionException",
    CannotCreateSessionException,
    (),
    None,
    (("reason", (), IcePy._t_string, False, 0),))

setattr(CannotCreateSessionException, '_ice_type', _Glacier2_CannotCreateSessionException_t)

__all__ = ["CannotCreateSessionException", "_Glacier2_CannotCreateSessionException_t"]
