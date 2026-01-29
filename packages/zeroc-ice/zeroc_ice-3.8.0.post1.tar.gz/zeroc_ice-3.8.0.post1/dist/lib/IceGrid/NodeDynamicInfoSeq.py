# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.NodeDynamicInfo import _IceGrid_NodeDynamicInfo_t

_IceGrid_NodeDynamicInfoSeq_t = IcePy.defineSequence("::IceGrid::NodeDynamicInfoSeq", (), _IceGrid_NodeDynamicInfo_t)

__all__ = ["_IceGrid_NodeDynamicInfoSeq_t"]
