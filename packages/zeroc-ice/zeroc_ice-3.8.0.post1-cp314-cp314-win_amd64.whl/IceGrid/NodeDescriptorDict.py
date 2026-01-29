# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.NodeDescriptor import _IceGrid_NodeDescriptor_t

_IceGrid_NodeDescriptorDict_t = IcePy.defineDictionary("::IceGrid::NodeDescriptorDict", (), IcePy._t_string, _IceGrid_NodeDescriptor_t)

__all__ = ["_IceGrid_NodeDescriptorDict_t"]
