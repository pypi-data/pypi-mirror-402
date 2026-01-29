# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.ServerDescriptor_forward import _IceGrid_ServerDescriptor_t

_IceGrid_ServerDescriptorSeq_t = IcePy.defineSequence("::IceGrid::ServerDescriptorSeq", (), _IceGrid_ServerDescriptor_t)

__all__ = ["_IceGrid_ServerDescriptorSeq_t"]
