# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.StringSeq import _Ice_StringSeq_t

from IceGrid.CommunicatorDescriptor_forward import _IceGrid_CommunicatorDescriptor_t

from IceGrid.StringStringDict import _IceGrid_StringStringDict_t

from dataclasses import dataclass
from dataclasses import field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IceGrid.CommunicatorDescriptor import CommunicatorDescriptor


@dataclass
class TemplateDescriptor:
    """
    Describes a template for a server or an IceBox service.
    
    Attributes
    ----------
    descriptor : CommunicatorDescriptor | None
        The communicator.
    parameters : list[str]
        The parameters required to instantiate the template.
    parameterDefaults : dict[str, str]
        The parameters' default values.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::TemplateDescriptor``.
    """
    descriptor: CommunicatorDescriptor | None = None
    parameters: list[str] = field(default_factory=list)
    parameterDefaults: dict[str, str] = field(default_factory=dict)

_IceGrid_TemplateDescriptor_t = IcePy.defineStruct(
    "::IceGrid::TemplateDescriptor",
    TemplateDescriptor,
    (),
    (
        ("descriptor", (), _IceGrid_CommunicatorDescriptor_t),
        ("parameters", (), _Ice_StringSeq_t),
        ("parameterDefaults", (), _IceGrid_StringStringDict_t)
    ))

__all__ = ["TemplateDescriptor", "_IceGrid_TemplateDescriptor_t"]
