# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.NodeUpdateDescriptor import _IceGrid_NodeUpdateDescriptor_t

_IceGrid_NodeUpdateDescriptorSeq_t = IcePy.defineSequence("::IceGrid::NodeUpdateDescriptorSeq", (), _IceGrid_NodeUpdateDescriptor_t)

__all__ = ["_IceGrid_NodeUpdateDescriptorSeq_t"]
