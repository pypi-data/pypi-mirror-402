# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.DistributionDescriptor import DistributionDescriptor
from IceGrid.DistributionDescriptor import _IceGrid_DistributionDescriptor_t

from IceGrid.NodeDescriptorDict import _IceGrid_NodeDescriptorDict_t

from IceGrid.PropertySetDescriptorDict import _IceGrid_PropertySetDescriptorDict_t

from IceGrid.ReplicaGroupDescriptorSeq import _IceGrid_ReplicaGroupDescriptorSeq_t

from IceGrid.StringStringDict import _IceGrid_StringStringDict_t

from IceGrid.TemplateDescriptorDict import _IceGrid_TemplateDescriptorDict_t

from dataclasses import dataclass
from dataclasses import field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IceGrid.NodeDescriptor import NodeDescriptor
    from IceGrid.PropertySetDescriptor import PropertySetDescriptor
    from IceGrid.ReplicaGroupDescriptor import ReplicaGroupDescriptor
    from IceGrid.TemplateDescriptor import TemplateDescriptor


@dataclass
class ApplicationDescriptor:
    """
    Describes an application.
    
    Attributes
    ----------
    name : str
        The application name.
    variables : dict[str, str]
        The variables defined in the application descriptor.
    replicaGroups : list[ReplicaGroupDescriptor]
        The replica groups.
    serverTemplates : dict[str, TemplateDescriptor]
        The server templates.
    serviceTemplates : dict[str, TemplateDescriptor]
        The service templates.
    nodes : dict[str, NodeDescriptor]
        The node descriptors.
    distrib : DistributionDescriptor
        The application distribution.
    description : str
        The description of this application.
    propertySets : dict[str, PropertySetDescriptor]
        Property set descriptors.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::ApplicationDescriptor``.
    """
    name: str = ""
    variables: dict[str, str] = field(default_factory=dict)
    replicaGroups: list[ReplicaGroupDescriptor] = field(default_factory=list)
    serverTemplates: dict[str, TemplateDescriptor] = field(default_factory=dict)
    serviceTemplates: dict[str, TemplateDescriptor] = field(default_factory=dict)
    nodes: dict[str, NodeDescriptor] = field(default_factory=dict)
    distrib: DistributionDescriptor = field(default_factory=DistributionDescriptor)
    description: str = ""
    propertySets: dict[str, PropertySetDescriptor] = field(default_factory=dict)

_IceGrid_ApplicationDescriptor_t = IcePy.defineStruct(
    "::IceGrid::ApplicationDescriptor",
    ApplicationDescriptor,
    (),
    (
        ("name", (), IcePy._t_string),
        ("variables", (), _IceGrid_StringStringDict_t),
        ("replicaGroups", (), _IceGrid_ReplicaGroupDescriptorSeq_t),
        ("serverTemplates", (), _IceGrid_TemplateDescriptorDict_t),
        ("serviceTemplates", (), _IceGrid_TemplateDescriptorDict_t),
        ("nodes", (), _IceGrid_NodeDescriptorDict_t),
        ("distrib", (), _IceGrid_DistributionDescriptor_t),
        ("description", (), IcePy._t_string),
        ("propertySets", (), _IceGrid_PropertySetDescriptorDict_t)
    ))

__all__ = ["ApplicationDescriptor", "_IceGrid_ApplicationDescriptor_t"]
