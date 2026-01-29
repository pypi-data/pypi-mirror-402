# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.PropertyDescriptor import _IceGrid_PropertyDescriptor_t

_IceGrid_PropertyDescriptorSeq_t = IcePy.defineSequence("::IceGrid::PropertyDescriptorSeq", (), _IceGrid_PropertyDescriptor_t)

__all__ = ["_IceGrid_PropertyDescriptorSeq_t"]
