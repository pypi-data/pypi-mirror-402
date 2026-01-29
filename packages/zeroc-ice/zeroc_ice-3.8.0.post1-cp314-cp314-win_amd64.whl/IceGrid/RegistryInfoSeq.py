# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.RegistryInfo import _IceGrid_RegistryInfo_t

_IceGrid_RegistryInfoSeq_t = IcePy.defineSequence("::IceGrid::RegistryInfoSeq", (), _IceGrid_RegistryInfo_t)

__all__ = ["_IceGrid_RegistryInfoSeq_t"]
