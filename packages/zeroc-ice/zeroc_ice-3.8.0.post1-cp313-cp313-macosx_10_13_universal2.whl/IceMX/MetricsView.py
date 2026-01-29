# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceMX.MetricsMap import _IceMX_MetricsMap_t

_IceMX_MetricsView_t = IcePy.defineDictionary("::IceMX::MetricsView", (), IcePy._t_string, _IceMX_MetricsMap_t)

__all__ = ["_IceMX_MetricsView_t"]
