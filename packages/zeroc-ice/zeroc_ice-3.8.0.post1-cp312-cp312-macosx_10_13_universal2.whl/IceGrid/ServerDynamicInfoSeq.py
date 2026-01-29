# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.ServerDynamicInfo import _IceGrid_ServerDynamicInfo_t

_IceGrid_ServerDynamicInfoSeq_t = IcePy.defineSequence("::IceGrid::ServerDynamicInfoSeq", (), _IceGrid_ServerDynamicInfo_t)

__all__ = ["_IceGrid_ServerDynamicInfoSeq_t"]
