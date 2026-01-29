# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class BadQoS(UserException):
    """
    The exception that is thrown when attempting to subscribe with an invalid ``QoS``.
    
    Attributes
    ----------
    reason : str
        The reason for the failure.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceStorm::BadQoS``.
    """
    reason: str = ""

    _ice_id = "::IceStorm::BadQoS"

_IceStorm_BadQoS_t = IcePy.defineException(
    "::IceStorm::BadQoS",
    BadQoS,
    (),
    None,
    (("reason", (), IcePy._t_string, False, 0),))

setattr(BadQoS, '_ice_type', _IceStorm_BadQoS_t)

__all__ = ["BadQoS", "_IceStorm_BadQoS_t"]
