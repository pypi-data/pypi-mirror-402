# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class PermissionDeniedException(UserException):
    """
    The exception that is thrown when a client is not allowed to create a session.
    
    Attributes
    ----------
    reason : str
        The reason why permission was denied.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::Glacier2::PermissionDeniedException``.
    """
    reason: str = ""

    _ice_id = "::Glacier2::PermissionDeniedException"

_Glacier2_PermissionDeniedException_t = IcePy.defineException(
    "::Glacier2::PermissionDeniedException",
    PermissionDeniedException,
    (),
    None,
    (("reason", (), IcePy._t_string, False, 0),))

setattr(PermissionDeniedException, '_ice_type', _Glacier2_PermissionDeniedException_t)

__all__ = ["PermissionDeniedException", "_Glacier2_PermissionDeniedException_t"]
