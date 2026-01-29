# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceMX.ChildInvocationMetrics import ChildInvocationMetrics

from IceMX.ChildInvocationMetrics_forward import _IceMX_ChildInvocationMetrics_t

from IceMX.RemoteMetrics_forward import _IceMX_RemoteMetrics_t

from dataclasses import dataclass

@dataclass(eq=False)
class RemoteMetrics(ChildInvocationMetrics):
    """
    Provides information on invocations that are specifically sent over Ice connections. Remote metrics are embedded
    within :class:`IceMX.InvocationMetrics`.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceMX::RemoteMetrics``.
    """

    @staticmethod
    def ice_staticId() -> str:
        return "::IceMX::RemoteMetrics"

_IceMX_RemoteMetrics_t = IcePy.defineValue(
    "::IceMX::RemoteMetrics",
    RemoteMetrics,
    -1,
    (),
    False,
    _IceMX_ChildInvocationMetrics_t,
    ())

setattr(RemoteMetrics, '_ice_type', _IceMX_RemoteMetrics_t)

__all__ = ["RemoteMetrics", "_IceMX_RemoteMetrics_t"]
