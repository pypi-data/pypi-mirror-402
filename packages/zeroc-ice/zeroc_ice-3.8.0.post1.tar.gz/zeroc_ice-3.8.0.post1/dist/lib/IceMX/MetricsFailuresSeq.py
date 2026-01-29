# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceMX.MetricsFailures import _IceMX_MetricsFailures_t

_IceMX_MetricsFailuresSeq_t = IcePy.defineSequence("::IceMX::MetricsFailuresSeq", (), _IceMX_MetricsFailures_t)

__all__ = ["_IceMX_MetricsFailuresSeq_t"]
