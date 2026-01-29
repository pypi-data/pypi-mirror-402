# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.ReplicaGroupDescriptor import _IceGrid_ReplicaGroupDescriptor_t

_IceGrid_ReplicaGroupDescriptorSeq_t = IcePy.defineSequence("::IceGrid::ReplicaGroupDescriptorSeq", (), _IceGrid_ReplicaGroupDescriptor_t)

__all__ = ["_IceGrid_ReplicaGroupDescriptorSeq_t"]
