# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.ApplicationInfo import _IceGrid_ApplicationInfo_t

_IceGrid_ApplicationInfoSeq_t = IcePy.defineSequence("::IceGrid::ApplicationInfoSeq", (), _IceGrid_ApplicationInfo_t)

__all__ = ["_IceGrid_ApplicationInfoSeq_t"]
