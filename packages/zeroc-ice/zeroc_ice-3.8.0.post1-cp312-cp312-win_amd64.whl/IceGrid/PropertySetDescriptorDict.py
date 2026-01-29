# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.PropertySetDescriptor import _IceGrid_PropertySetDescriptor_t

_IceGrid_PropertySetDescriptorDict_t = IcePy.defineDictionary("::IceGrid::PropertySetDescriptorDict", (), IcePy._t_string, _IceGrid_PropertySetDescriptor_t)

__all__ = ["_IceGrid_PropertySetDescriptorDict_t"]
