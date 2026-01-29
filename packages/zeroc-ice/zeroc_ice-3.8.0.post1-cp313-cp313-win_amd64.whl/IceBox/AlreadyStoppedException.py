# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class AlreadyStoppedException(UserException):
    """
    The exception that is thrown when attempting to stop a service that is already stopped.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceBox::AlreadyStoppedException``.
    """

    _ice_id = "::IceBox::AlreadyStoppedException"

_IceBox_AlreadyStoppedException_t = IcePy.defineException(
    "::IceBox::AlreadyStoppedException",
    AlreadyStoppedException,
    (),
    None,
    ())

setattr(AlreadyStoppedException, '_ice_type', _IceBox_AlreadyStoppedException_t)

__all__ = ["AlreadyStoppedException", "_IceBox_AlreadyStoppedException_t"]
