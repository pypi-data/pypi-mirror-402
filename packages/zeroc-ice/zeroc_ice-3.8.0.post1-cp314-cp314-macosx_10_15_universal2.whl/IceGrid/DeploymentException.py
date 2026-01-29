# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class DeploymentException(UserException):
    """
    The exception that is thrown when IceGrid cannot deploy a server.
    
    Attributes
    ----------
    reason : str
        The reason for the failure.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceGrid::DeploymentException``.
    """
    reason: str = ""

    _ice_id = "::IceGrid::DeploymentException"

_IceGrid_DeploymentException_t = IcePy.defineException(
    "::IceGrid::DeploymentException",
    DeploymentException,
    (),
    None,
    (("reason", (), IcePy._t_string, False, 0),))

setattr(DeploymentException, '_ice_type', _IceGrid_DeploymentException_t)

__all__ = ["DeploymentException", "_IceGrid_DeploymentException_t"]
