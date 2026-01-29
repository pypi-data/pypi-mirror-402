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
class ObjectExistsException(UserException):
    """
    The exception that is thrown when a well-known object is already registered.
    
    Attributes
    ----------
    id : Identity
        The identity of the object.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceGrid::ObjectExistsException``.
    """
    id: Identity = field(default_factory=Identity)

    _ice_id = "::IceGrid::ObjectExistsException"

_IceGrid_ObjectExistsException_t = IcePy.defineException(
    "::IceGrid::ObjectExistsException",
    ObjectExistsException,
    (),
    None,
    (("id", (), _Ice_Identity_t, False, 0),))

setattr(ObjectExistsException, '_ice_type', _IceGrid_ObjectExistsException_t)

__all__ = ["ObjectExistsException", "_IceGrid_ObjectExistsException_t"]
