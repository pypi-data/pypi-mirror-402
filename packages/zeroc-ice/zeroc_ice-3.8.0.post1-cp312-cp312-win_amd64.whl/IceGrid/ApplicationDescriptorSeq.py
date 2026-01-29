# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.ApplicationDescriptor import _IceGrid_ApplicationDescriptor_t

_IceGrid_ApplicationDescriptorSeq_t = IcePy.defineSequence("::IceGrid::ApplicationDescriptorSeq", (), _IceGrid_ApplicationDescriptor_t)

__all__ = ["_IceGrid_ApplicationDescriptorSeq_t"]
