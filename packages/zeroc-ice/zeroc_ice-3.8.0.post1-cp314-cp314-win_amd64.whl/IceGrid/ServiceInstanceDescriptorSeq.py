# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.ServiceInstanceDescriptor import _IceGrid_ServiceInstanceDescriptor_t

_IceGrid_ServiceInstanceDescriptorSeq_t = IcePy.defineSequence("::IceGrid::ServiceInstanceDescriptorSeq", (), _IceGrid_ServiceInstanceDescriptor_t)

__all__ = ["_IceGrid_ServiceInstanceDescriptorSeq_t"]
