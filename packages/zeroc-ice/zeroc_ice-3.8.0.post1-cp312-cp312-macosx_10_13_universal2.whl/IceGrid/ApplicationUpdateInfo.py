# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.ApplicationUpdateDescriptor import ApplicationUpdateDescriptor
from IceGrid.ApplicationUpdateDescriptor import _IceGrid_ApplicationUpdateDescriptor_t

from dataclasses import dataclass
from dataclasses import field


@dataclass
class ApplicationUpdateInfo:
    """
    Information about updates to an IceGrid application.
    
    Attributes
    ----------
    updateTime : int
        The update time.
    updateUser : str
        The user who updated the application.
    revision : int
        The application revision number.
    descriptor : ApplicationUpdateDescriptor
        The update descriptor.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::ApplicationUpdateInfo``.
    """
    updateTime: int = 0
    updateUser: str = ""
    revision: int = 0
    descriptor: ApplicationUpdateDescriptor = field(default_factory=ApplicationUpdateDescriptor)

_IceGrid_ApplicationUpdateInfo_t = IcePy.defineStruct(
    "::IceGrid::ApplicationUpdateInfo",
    ApplicationUpdateInfo,
    (),
    (
        ("updateTime", (), IcePy._t_long),
        ("updateUser", (), IcePy._t_string),
        ("revision", (), IcePy._t_int),
        ("descriptor", (), _IceGrid_ApplicationUpdateDescriptor_t)
    ))

__all__ = ["ApplicationUpdateInfo", "_IceGrid_ApplicationUpdateInfo_t"]
