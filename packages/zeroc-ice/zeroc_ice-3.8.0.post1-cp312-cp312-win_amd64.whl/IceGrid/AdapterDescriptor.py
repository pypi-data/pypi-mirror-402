# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.ObjectDescriptorSeq import _IceGrid_ObjectDescriptorSeq_t

from dataclasses import dataclass
from dataclasses import field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IceGrid.ObjectDescriptor import ObjectDescriptor


@dataclass
class AdapterDescriptor:
    """
    Describes an indirect object adapter.
    
    Attributes
    ----------
    name : str
        The object adapter name.
    description : str
        A description of this object adapter.
    id : str
        The adapter ID.
    replicaGroupId : str
        The replica group ID. It's empty when the adapter is not part of a replica group.
    priority : str
        The adapter priority. Only relevant when the adapter is in a replica group.
    registerProcess : bool
        When ``true``, the object adapter registers a process object.
    serverLifetime : bool
        When ``true``, the lifetime of this object adapter is the same of the server lifetime. This information is
        used by the IceGrid node to figure out the server state: the server is active when all its "server lifetime"
        adapters are active.
    objects : list[ObjectDescriptor]
        The descriptors of well-known objects.
    allocatables : list[ObjectDescriptor]
        The descriptors of allocatable objects.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::AdapterDescriptor``.
    """
    name: str = ""
    description: str = ""
    id: str = ""
    replicaGroupId: str = ""
    priority: str = ""
    registerProcess: bool = False
    serverLifetime: bool = False
    objects: list[ObjectDescriptor] = field(default_factory=list)
    allocatables: list[ObjectDescriptor] = field(default_factory=list)

_IceGrid_AdapterDescriptor_t = IcePy.defineStruct(
    "::IceGrid::AdapterDescriptor",
    AdapterDescriptor,
    (),
    (
        ("name", (), IcePy._t_string),
        ("description", (), IcePy._t_string),
        ("id", (), IcePy._t_string),
        ("replicaGroupId", (), IcePy._t_string),
        ("priority", (), IcePy._t_string),
        ("registerProcess", (), IcePy._t_bool),
        ("serverLifetime", (), IcePy._t_bool),
        ("objects", (), _IceGrid_ObjectDescriptorSeq_t),
        ("allocatables", (), _IceGrid_ObjectDescriptorSeq_t)
    ))

__all__ = ["AdapterDescriptor", "_IceGrid_AdapterDescriptor_t"]
