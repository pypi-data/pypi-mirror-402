# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.AdapterDescriptor import _IceGrid_AdapterDescriptor_t

_IceGrid_AdapterDescriptorSeq_t = IcePy.defineSequence("::IceGrid::AdapterDescriptorSeq", (), _IceGrid_AdapterDescriptor_t)

__all__ = ["_IceGrid_AdapterDescriptorSeq_t"]
