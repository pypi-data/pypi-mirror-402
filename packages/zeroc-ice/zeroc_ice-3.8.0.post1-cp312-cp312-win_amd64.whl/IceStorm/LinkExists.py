# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class LinkExists(UserException):
    """
    The exception that is thrown when attempting to create a link that already exists.
    
    Attributes
    ----------
    name : str
        The name of the linked topic.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceStorm::LinkExists``.
    """
    name: str = ""

    _ice_id = "::IceStorm::LinkExists"

_IceStorm_LinkExists_t = IcePy.defineException(
    "::IceStorm::LinkExists",
    LinkExists,
    (),
    None,
    (("name", (), IcePy._t_string, False, 0),))

setattr(LinkExists, '_ice_type', _IceStorm_LinkExists_t)

__all__ = ["LinkExists", "_IceStorm_LinkExists_t"]
