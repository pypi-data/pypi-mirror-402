# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceMX.Metrics_forward import _IceMX_Metrics_t

_IceMX_MetricsMap_t = IcePy.defineSequence("::IceMX::MetricsMap", (), _IceMX_Metrics_t)

__all__ = ["_IceMX_MetricsMap_t"]
