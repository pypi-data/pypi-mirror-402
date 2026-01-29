# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.StringSeq import _Ice_StringSeq_t

from IceGrid.BoxedDistributionDescriptor_forward import _IceGrid_BoxedDistributionDescriptor_t

from IceGrid.BoxedString_forward import _IceGrid_BoxedString_t

from IceGrid.NodeUpdateDescriptorSeq import _IceGrid_NodeUpdateDescriptorSeq_t

from IceGrid.PropertySetDescriptorDict import _IceGrid_PropertySetDescriptorDict_t

from IceGrid.ReplicaGroupDescriptorSeq import _IceGrid_ReplicaGroupDescriptorSeq_t

from IceGrid.StringStringDict import _IceGrid_StringStringDict_t

from IceGrid.TemplateDescriptorDict import _IceGrid_TemplateDescriptorDict_t

from dataclasses import dataclass
from dataclasses import field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IceGrid.BoxedDistributionDescriptor import BoxedDistributionDescriptor
    from IceGrid.BoxedString import BoxedString
    from IceGrid.NodeUpdateDescriptor import NodeUpdateDescriptor
    from IceGrid.PropertySetDescriptor import PropertySetDescriptor
    from IceGrid.ReplicaGroupDescriptor import ReplicaGroupDescriptor
    from IceGrid.TemplateDescriptor import TemplateDescriptor


@dataclass
class ApplicationUpdateDescriptor:
    """
    An application update descriptor to describe the updates to apply to a deployed application.
    
    Attributes
    ----------
    name : str
        The name of the application to update.
    description : BoxedString | None
        The updated description (or null if the description wasn't updated).
    distrib : BoxedDistributionDescriptor | None
        The updated distribution application descriptor.
    variables : dict[str, str]
        The variables to update.
    removeVariables : list[str]
        The variables to remove.
    propertySets : dict[str, PropertySetDescriptor]
        The property sets to update.
    removePropertySets : list[str]
        The property sets to remove.
    replicaGroups : list[ReplicaGroupDescriptor]
        The replica groups to update.
    removeReplicaGroups : list[str]
        The replica groups to remove.
    serverTemplates : dict[str, TemplateDescriptor]
        The server templates to update.
    removeServerTemplates : list[str]
        The IDs of the server template to remove.
    serviceTemplates : dict[str, TemplateDescriptor]
        The service templates to update.
    removeServiceTemplates : list[str]
        The IDs of the service template to remove.
    nodes : list[NodeUpdateDescriptor]
        The application nodes to update.
    removeNodes : list[str]
        The nodes to remove.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::ApplicationUpdateDescriptor``.
    """
    name: str = ""
    description: BoxedString | None = None
    distrib: BoxedDistributionDescriptor | None = None
    variables: dict[str, str] = field(default_factory=dict)
    removeVariables: list[str] = field(default_factory=list)
    propertySets: dict[str, PropertySetDescriptor] = field(default_factory=dict)
    removePropertySets: list[str] = field(default_factory=list)
    replicaGroups: list[ReplicaGroupDescriptor] = field(default_factory=list)
    removeReplicaGroups: list[str] = field(default_factory=list)
    serverTemplates: dict[str, TemplateDescriptor] = field(default_factory=dict)
    removeServerTemplates: list[str] = field(default_factory=list)
    serviceTemplates: dict[str, TemplateDescriptor] = field(default_factory=dict)
    removeServiceTemplates: list[str] = field(default_factory=list)
    nodes: list[NodeUpdateDescriptor] = field(default_factory=list)
    removeNodes: list[str] = field(default_factory=list)

_IceGrid_ApplicationUpdateDescriptor_t = IcePy.defineStruct(
    "::IceGrid::ApplicationUpdateDescriptor",
    ApplicationUpdateDescriptor,
    (),
    (
        ("name", (), IcePy._t_string),
        ("description", (), _IceGrid_BoxedString_t),
        ("distrib", (), _IceGrid_BoxedDistributionDescriptor_t),
        ("variables", (), _IceGrid_StringStringDict_t),
        ("removeVariables", (), _Ice_StringSeq_t),
        ("propertySets", (), _IceGrid_PropertySetDescriptorDict_t),
        ("removePropertySets", (), _Ice_StringSeq_t),
        ("replicaGroups", (), _IceGrid_ReplicaGroupDescriptorSeq_t),
        ("removeReplicaGroups", (), _Ice_StringSeq_t),
        ("serverTemplates", (), _IceGrid_TemplateDescriptorDict_t),
        ("removeServerTemplates", (), _Ice_StringSeq_t),
        ("serviceTemplates", (), _IceGrid_TemplateDescriptorDict_t),
        ("removeServiceTemplates", (), _Ice_StringSeq_t),
        ("nodes", (), _IceGrid_NodeUpdateDescriptorSeq_t),
        ("removeNodes", (), _Ice_StringSeq_t)
    ))

__all__ = ["ApplicationUpdateDescriptor", "_IceGrid_ApplicationUpdateDescriptor_t"]
