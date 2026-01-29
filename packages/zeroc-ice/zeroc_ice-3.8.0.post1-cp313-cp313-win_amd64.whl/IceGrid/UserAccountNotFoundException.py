# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class UserAccountNotFoundException(UserException):
    """
    The exception that is thrown when a user account for a given session identifier can't be found.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceGrid::UserAccountNotFoundException``.
    """

    _ice_id = "::IceGrid::UserAccountNotFoundException"

_IceGrid_UserAccountNotFoundException_t = IcePy.defineException(
    "::IceGrid::UserAccountNotFoundException",
    UserAccountNotFoundException,
    (),
    None,
    ())

setattr(UserAccountNotFoundException, '_ice_type', _IceGrid_UserAccountNotFoundException_t)

__all__ = ["UserAccountNotFoundException", "_IceGrid_UserAccountNotFoundException_t"]
