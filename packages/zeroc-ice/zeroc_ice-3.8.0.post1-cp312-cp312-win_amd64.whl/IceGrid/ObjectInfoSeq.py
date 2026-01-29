# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.ObjectInfo import _IceGrid_ObjectInfo_t

_IceGrid_ObjectInfoSeq_t = IcePy.defineSequence("::IceGrid::ObjectInfoSeq", (), _IceGrid_ObjectInfo_t)

__all__ = ["_IceGrid_ObjectInfoSeq_t"]
