# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.TemplateDescriptor import _IceGrid_TemplateDescriptor_t

_IceGrid_TemplateDescriptorDict_t = IcePy.defineDictionary("::IceGrid::TemplateDescriptorDict", (), IcePy._t_string, _IceGrid_TemplateDescriptor_t)

__all__ = ["_IceGrid_TemplateDescriptorDict_t"]
