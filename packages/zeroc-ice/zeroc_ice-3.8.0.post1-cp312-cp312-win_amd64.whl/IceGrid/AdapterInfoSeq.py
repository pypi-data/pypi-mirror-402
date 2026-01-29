# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.AdapterInfo import _IceGrid_AdapterInfo_t

_IceGrid_AdapterInfoSeq_t = IcePy.defineSequence("::IceGrid::AdapterInfoSeq", (), _IceGrid_AdapterInfo_t)

__all__ = ["_IceGrid_AdapterInfoSeq_t"]
