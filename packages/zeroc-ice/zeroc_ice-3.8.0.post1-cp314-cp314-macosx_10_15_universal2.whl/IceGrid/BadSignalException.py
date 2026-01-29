# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class BadSignalException(UserException):
    """
    The exception that is thrown when an unknown signal is sent to a server.
    
    Attributes
    ----------
    reason : str
        The details of the unknown signal.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceGrid::BadSignalException``.
    """
    reason: str = ""

    _ice_id = "::IceGrid::BadSignalException"

_IceGrid_BadSignalException_t = IcePy.defineException(
    "::IceGrid::BadSignalException",
    BadSignalException,
    (),
    None,
    (("reason", (), IcePy._t_string, False, 0),))

setattr(BadSignalException, '_ice_type', _IceGrid_BadSignalException_t)

__all__ = ["BadSignalException", "_IceGrid_BadSignalException_t"]
