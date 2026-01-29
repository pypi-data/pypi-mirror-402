# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.PropertyDescriptorSeq import _IceGrid_PropertyDescriptorSeq_t

from dataclasses import dataclass
from dataclasses import field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IceGrid.PropertyDescriptor import PropertyDescriptor


@dataclass
class DbEnvDescriptor:
    """
    A Freeze database environment descriptor (deprecated, no longer used).
    
    Attributes
    ----------
    name : str
        The name of the database environment.
    description : str
        The description of this database environment.
    dbHome : str
        The home of the database environment.
    properties : list[PropertyDescriptor]
        The configuration properties of the database environment.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::DbEnvDescriptor``.
    """
    name: str = ""
    description: str = ""
    dbHome: str = ""
    properties: list[PropertyDescriptor] = field(default_factory=list)

_IceGrid_DbEnvDescriptor_t = IcePy.defineStruct(
    "::IceGrid::DbEnvDescriptor",
    DbEnvDescriptor,
    (),
    (
        ("name", (), IcePy._t_string),
        ("description", (), IcePy._t_string),
        ("dbHome", (), IcePy._t_string),
        ("properties", (), _IceGrid_PropertyDescriptorSeq_t)
    ))

__all__ = ["DbEnvDescriptor", "_IceGrid_DbEnvDescriptor_t"]
