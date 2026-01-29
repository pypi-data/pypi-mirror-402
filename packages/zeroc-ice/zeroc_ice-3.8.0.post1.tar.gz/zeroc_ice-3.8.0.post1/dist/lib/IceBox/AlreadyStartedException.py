# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class AlreadyStartedException(UserException):
    """
    The exception that is thrown when attempting to start a service that is already running.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceBox::AlreadyStartedException``.
    """

    _ice_id = "::IceBox::AlreadyStartedException"

_IceBox_AlreadyStartedException_t = IcePy.defineException(
    "::IceBox::AlreadyStartedException",
    AlreadyStartedException,
    (),
    None,
    ())

setattr(AlreadyStartedException, '_ice_type', _IceBox_AlreadyStartedException_t)

__all__ = ["AlreadyStartedException", "_IceBox_AlreadyStartedException_t"]
