# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.Identity import Identity
from Ice.Identity import _Ice_Identity_t

from Ice.UserException import UserException

from dataclasses import dataclass
from dataclasses import field


@dataclass
class ObjectNotRegisteredException(UserException):
    """
    The exception that is thrown when a well-known object is not registered.
    
    Attributes
    ----------
    id : Identity
        The identity of the object.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceGrid::ObjectNotRegisteredException``.
    """
    id: Identity = field(default_factory=Identity)

    _ice_id = "::IceGrid::ObjectNotRegisteredException"

_IceGrid_ObjectNotRegisteredException_t = IcePy.defineException(
    "::IceGrid::ObjectNotRegisteredException",
    ObjectNotRegisteredException,
    (),
    None,
    (("id", (), _Ice_Identity_t, False, 0),))

setattr(ObjectNotRegisteredException, '_ice_type', _IceGrid_ObjectNotRegisteredException_t)

__all__ = ["ObjectNotRegisteredException", "_IceGrid_ObjectNotRegisteredException_t"]
