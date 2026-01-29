# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class ParseException(UserException):
    """
    The exception that is thrown when an error occurs during the parsing of an IceGrid XML file.
    
    Attributes
    ----------
    reason : str
        The reason for the failure.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceGrid::ParseException``.
    """
    reason: str = ""

    _ice_id = "::IceGrid::ParseException"

_IceGrid_ParseException_t = IcePy.defineException(
    "::IceGrid::ParseException",
    ParseException,
    (),
    None,
    (("reason", (), IcePy._t_string, False, 0),))

setattr(ParseException, '_ice_type', _IceGrid_ParseException_t)

__all__ = ["ParseException", "_IceGrid_ParseException_t"]
