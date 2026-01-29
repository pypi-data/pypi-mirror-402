# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class TopicExists(UserException):
    """
    The exception that is thrown when attempting to create a topic that already exists.
    
    Attributes
    ----------
    name : str
        The name of the topic that already exists.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceStorm::TopicExists``.
    """
    name: str = ""

    _ice_id = "::IceStorm::TopicExists"

_IceStorm_TopicExists_t = IcePy.defineException(
    "::IceStorm::TopicExists",
    TopicExists,
    (),
    None,
    (("name", (), IcePy._t_string, False, 0),))

setattr(TopicExists, '_ice_type', _IceStorm_TopicExists_t)

__all__ = ["TopicExists", "_IceStorm_TopicExists_t"]
