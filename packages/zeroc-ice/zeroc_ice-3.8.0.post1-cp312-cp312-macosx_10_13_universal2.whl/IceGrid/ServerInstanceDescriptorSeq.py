# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.ServerInstanceDescriptor import _IceGrid_ServerInstanceDescriptor_t

_IceGrid_ServerInstanceDescriptorSeq_t = IcePy.defineSequence("::IceGrid::ServerInstanceDescriptorSeq", (), _IceGrid_ServerInstanceDescriptor_t)

__all__ = ["_IceGrid_ServerInstanceDescriptorSeq_t"]
