# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.ObjectDescriptor import _IceGrid_ObjectDescriptor_t

_IceGrid_ObjectDescriptorSeq_t = IcePy.defineSequence("::IceGrid::ObjectDescriptorSeq", (), _IceGrid_ObjectDescriptor_t)

__all__ = ["_IceGrid_ObjectDescriptorSeq_t"]
