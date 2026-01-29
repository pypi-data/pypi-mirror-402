# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class ApplicationNotExistException(UserException):
    """
    The exception that is thrown when IceGrid does not know an application with the provided name.
    
    Attributes
    ----------
    name : str
        The name of the application.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceGrid::ApplicationNotExistException``.
    """
    name: str = ""

    _ice_id = "::IceGrid::ApplicationNotExistException"

_IceGrid_ApplicationNotExistException_t = IcePy.defineException(
    "::IceGrid::ApplicationNotExistException",
    ApplicationNotExistException,
    (),
    None,
    (("name", (), IcePy._t_string, False, 0),))

setattr(ApplicationNotExistException, '_ice_type', _IceGrid_ApplicationNotExistException_t)

__all__ = ["ApplicationNotExistException", "_IceGrid_ApplicationNotExistException_t"]
