# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class AccessDeniedException(UserException):
    """
    The exception that is thrown when the registry update lock cannot be acquired.
    
    Attributes
    ----------
    lockUserId : str
        The id of the user holding the lock (if any).
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceGrid::AccessDeniedException``.
    """
    lockUserId: str = ""

    _ice_id = "::IceGrid::AccessDeniedException"

_IceGrid_AccessDeniedException_t = IcePy.defineException(
    "::IceGrid::AccessDeniedException",
    AccessDeniedException,
    (),
    None,
    (("lockUserId", (), IcePy._t_string, False, 0),))

setattr(AccessDeniedException, '_ice_type', _IceGrid_AccessDeniedException_t)

__all__ = ["AccessDeniedException", "_IceGrid_AccessDeniedException_t"]
