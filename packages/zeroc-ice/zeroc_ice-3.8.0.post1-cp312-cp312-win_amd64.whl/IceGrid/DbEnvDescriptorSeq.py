# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.DbEnvDescriptor import _IceGrid_DbEnvDescriptor_t

_IceGrid_DbEnvDescriptorSeq_t = IcePy.defineSequence("::IceGrid::DbEnvDescriptorSeq", (), _IceGrid_DbEnvDescriptor_t)

__all__ = ["_IceGrid_DbEnvDescriptorSeq_t"]
