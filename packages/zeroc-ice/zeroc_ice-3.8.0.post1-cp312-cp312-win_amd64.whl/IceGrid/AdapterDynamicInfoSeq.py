# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.AdapterDynamicInfo import _IceGrid_AdapterDynamicInfo_t

_IceGrid_AdapterDynamicInfoSeq_t = IcePy.defineSequence("::IceGrid::AdapterDynamicInfoSeq", (), _IceGrid_AdapterDynamicInfo_t)

__all__ = ["_IceGrid_AdapterDynamicInfoSeq_t"]
