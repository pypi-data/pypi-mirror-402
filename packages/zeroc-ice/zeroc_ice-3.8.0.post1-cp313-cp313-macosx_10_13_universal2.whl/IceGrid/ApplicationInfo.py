# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.ApplicationDescriptor import ApplicationDescriptor
from IceGrid.ApplicationDescriptor import _IceGrid_ApplicationDescriptor_t

from dataclasses import dataclass
from dataclasses import field


@dataclass
class ApplicationInfo:
    """
    Information about an IceGrid application.
    
    Attributes
    ----------
    uuid : str
        Unique application identifier.
    createTime : int
        The creation time.
    createUser : str
        The user who created the application.
    updateTime : int
        The last update time.
    updateUser : str
        The user who updated the application.
    revision : int
        The application revision number.
    descriptor : ApplicationDescriptor
        The application descriptor.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::ApplicationInfo``.
    """
    uuid: str = ""
    createTime: int = 0
    createUser: str = ""
    updateTime: int = 0
    updateUser: str = ""
    revision: int = 0
    descriptor: ApplicationDescriptor = field(default_factory=ApplicationDescriptor)

_IceGrid_ApplicationInfo_t = IcePy.defineStruct(
    "::IceGrid::ApplicationInfo",
    ApplicationInfo,
    (),
    (
        ("uuid", (), IcePy._t_string),
        ("createTime", (), IcePy._t_long),
        ("createUser", (), IcePy._t_string),
        ("updateTime", (), IcePy._t_long),
        ("updateUser", (), IcePy._t_string),
        ("revision", (), IcePy._t_int),
        ("descriptor", (), _IceGrid_ApplicationDescriptor_t)
    ))

__all__ = ["ApplicationInfo", "_IceGrid_ApplicationInfo_t"]
