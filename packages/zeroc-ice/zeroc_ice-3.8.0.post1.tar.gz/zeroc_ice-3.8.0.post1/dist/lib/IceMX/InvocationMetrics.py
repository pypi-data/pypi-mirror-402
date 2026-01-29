# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceMX.InvocationMetrics_forward import _IceMX_InvocationMetrics_t

from IceMX.Metrics import Metrics

from IceMX.MetricsMap import _IceMX_MetricsMap_t

from IceMX.Metrics_forward import _IceMX_Metrics_t

from dataclasses import dataclass
from dataclasses import field

from typing import TYPE_CHECKING

@dataclass(eq=False)
class InvocationMetrics(Metrics):
    """
    Provide measurements for proxy invocations. Proxy invocations can either be sent over the wire or be collocated.
    
    Attributes
    ----------
    retry : int
        The number of retries for the invocations.
    userException : int
        The number of invocations that failed with a user exception.
    remotes : list[Metrics | None]
        The remote invocation metrics map.
    collocated : list[Metrics | None]
        The collocated invocation metrics map.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceMX::InvocationMetrics``.
    """
    retry: int = 0
    userException: int = 0
    remotes: list[Metrics | None] = field(default_factory=list)
    collocated: list[Metrics | None] = field(default_factory=list)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceMX::InvocationMetrics"

_IceMX_InvocationMetrics_t = IcePy.defineValue(
    "::IceMX::InvocationMetrics",
    InvocationMetrics,
    -1,
    (),
    False,
    _IceMX_Metrics_t,
    (
        ("retry", (), IcePy._t_int, False, 0),
        ("userException", (), IcePy._t_int, False, 0),
        ("remotes", (), _IceMX_MetricsMap_t, False, 0),
        ("collocated", (), _IceMX_MetricsMap_t, False, 0)
    ))

setattr(InvocationMetrics, '_ice_type', _IceMX_InvocationMetrics_t)

__all__ = ["InvocationMetrics", "_IceMX_InvocationMetrics_t"]
