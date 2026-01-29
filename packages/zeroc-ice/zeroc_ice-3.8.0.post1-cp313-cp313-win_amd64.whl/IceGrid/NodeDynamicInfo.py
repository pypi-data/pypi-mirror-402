# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.AdapterDynamicInfoSeq import _IceGrid_AdapterDynamicInfoSeq_t

from IceGrid.NodeInfo import NodeInfo
from IceGrid.NodeInfo import _IceGrid_NodeInfo_t

from IceGrid.ServerDynamicInfoSeq import _IceGrid_ServerDynamicInfoSeq_t

from dataclasses import dataclass
from dataclasses import field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IceGrid.AdapterDynamicInfo import AdapterDynamicInfo
    from IceGrid.ServerDynamicInfo import ServerDynamicInfo


@dataclass
class NodeDynamicInfo:
    """
    Dynamic information about the state of a node.
    
    Attributes
    ----------
    info : NodeInfo
        Some static information about the node.
    servers : list[ServerDynamicInfo]
        The dynamic information of the servers deployed on this node.
    adapters : list[AdapterDynamicInfo]
        The dynamic information of the adapters deployed on this node.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::NodeDynamicInfo``.
    """
    info: NodeInfo = field(default_factory=NodeInfo)
    servers: list[ServerDynamicInfo] = field(default_factory=list)
    adapters: list[AdapterDynamicInfo] = field(default_factory=list)

_IceGrid_NodeDynamicInfo_t = IcePy.defineStruct(
    "::IceGrid::NodeDynamicInfo",
    NodeDynamicInfo,
    (),
    (
        ("info", (), _IceGrid_NodeInfo_t),
        ("servers", (), _IceGrid_ServerDynamicInfoSeq_t),
        ("adapters", (), _IceGrid_AdapterDynamicInfoSeq_t)
    ))

__all__ = ["NodeDynamicInfo", "_IceGrid_NodeDynamicInfo_t"]
