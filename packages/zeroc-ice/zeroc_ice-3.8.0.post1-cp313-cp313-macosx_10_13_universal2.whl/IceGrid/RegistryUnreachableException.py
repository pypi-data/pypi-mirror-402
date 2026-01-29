# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class RegistryUnreachableException(UserException):
    """
    The exception that is thrown when IceGrid cannot reach a registry.
    
    Attributes
    ----------
    name : str
        The name of the registry that is not reachable.
    reason : str
        The reason why the registry couldn't be reached.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceGrid::RegistryUnreachableException``.
    """
    name: str = ""
    reason: str = ""

    _ice_id = "::IceGrid::RegistryUnreachableException"

_IceGrid_RegistryUnreachableException_t = IcePy.defineException(
    "::IceGrid::RegistryUnreachableException",
    RegistryUnreachableException,
    (),
    None,
    (
        ("name", (), IcePy._t_string, False, 0),
        ("reason", (), IcePy._t_string, False, 0)
    ))

setattr(RegistryUnreachableException, '_ice_type', _IceGrid_RegistryUnreachableException_t)

__all__ = ["RegistryUnreachableException", "_IceGrid_RegistryUnreachableException_t"]
