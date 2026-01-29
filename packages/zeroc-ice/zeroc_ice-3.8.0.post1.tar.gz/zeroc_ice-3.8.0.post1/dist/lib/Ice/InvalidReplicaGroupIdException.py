# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class InvalidReplicaGroupIdException(UserException):
    """
    The exception that is thrown when the provided replica group is invalid.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::Ice::InvalidReplicaGroupIdException``.
    """

    _ice_id = "::Ice::InvalidReplicaGroupIdException"

_Ice_InvalidReplicaGroupIdException_t = IcePy.defineException(
    "::Ice::InvalidReplicaGroupIdException",
    InvalidReplicaGroupIdException,
    (),
    None,
    ())

setattr(InvalidReplicaGroupIdException, '_ice_type', _Ice_InvalidReplicaGroupIdException_t)

__all__ = ["InvalidReplicaGroupIdException", "_Ice_InvalidReplicaGroupIdException_t"]
