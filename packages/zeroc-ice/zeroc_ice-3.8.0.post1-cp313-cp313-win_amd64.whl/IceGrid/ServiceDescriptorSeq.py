# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.ServiceDescriptor_forward import _IceGrid_ServiceDescriptor_t

_IceGrid_ServiceDescriptorSeq_t = IcePy.defineSequence("::IceGrid::ServiceDescriptorSeq", (), _IceGrid_ServiceDescriptor_t)

__all__ = ["_IceGrid_ServiceDescriptorSeq_t"]
