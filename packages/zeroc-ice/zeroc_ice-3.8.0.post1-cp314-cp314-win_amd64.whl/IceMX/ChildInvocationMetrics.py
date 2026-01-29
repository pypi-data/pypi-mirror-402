# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceMX.ChildInvocationMetrics_forward import _IceMX_ChildInvocationMetrics_t

from IceMX.Metrics import Metrics

from IceMX.Metrics_forward import _IceMX_Metrics_t

from dataclasses import dataclass

@dataclass(eq=False)
class ChildInvocationMetrics(Metrics):
    """
    Provides information on child invocations. A child invocation is either remote (sent over an Ice connection) or
    collocated. An invocation can have multiple child invocations if it is retried. Child invocation metrics are
    embedded within :class:`IceMX.InvocationMetrics`.
    
    Attributes
    ----------
    size : int
        The size of the invocation. This corresponds to the size of the marshaled input parameters.
    replySize : int
        The size of the invocation reply. This corresponds to the size of the marshaled output and return
        parameters.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceMX::ChildInvocationMetrics``.
    """
    size: int = 0
    replySize: int = 0

    @staticmethod
    def ice_staticId() -> str:
        return "::IceMX::ChildInvocationMetrics"

_IceMX_ChildInvocationMetrics_t = IcePy.defineValue(
    "::IceMX::ChildInvocationMetrics",
    ChildInvocationMetrics,
    -1,
    (),
    False,
    _IceMX_Metrics_t,
    (
        ("size", (), IcePy._t_long, False, 0),
        ("replySize", (), IcePy._t_long, False, 0)
    ))

setattr(ChildInvocationMetrics, '_ice_type', _IceMX_ChildInvocationMetrics_t)

__all__ = ["ChildInvocationMetrics", "_IceMX_ChildInvocationMetrics_t"]
