# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceMX.DispatchMetrics_forward import _IceMX_DispatchMetrics_t

from IceMX.Metrics import Metrics

from IceMX.Metrics_forward import _IceMX_Metrics_t

from dataclasses import dataclass

@dataclass(eq=False)
class DispatchMetrics(Metrics):
    """
    Provides information on servant dispatches.
    
    Attributes
    ----------
    userException : int
        The number of dispatches that failed with a user exception.
    size : int
        The size of the incoming requests. This corresponds to the size of the marshaled input parameters.
    replySize : int
        The size of the replies. This corresponds to the size of the marshaled output and return parameters.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceMX::DispatchMetrics``.
    """
    userException: int = 0
    size: int = 0
    replySize: int = 0

    @staticmethod
    def ice_staticId() -> str:
        return "::IceMX::DispatchMetrics"

_IceMX_DispatchMetrics_t = IcePy.defineValue(
    "::IceMX::DispatchMetrics",
    DispatchMetrics,
    -1,
    (),
    False,
    _IceMX_Metrics_t,
    (
        ("userException", (), IcePy._t_int, False, 0),
        ("size", (), IcePy._t_long, False, 0),
        ("replySize", (), IcePy._t_long, False, 0)
    ))

setattr(DispatchMetrics, '_ice_type', _IceMX_DispatchMetrics_t)

__all__ = ["DispatchMetrics", "_IceMX_DispatchMetrics_t"]
