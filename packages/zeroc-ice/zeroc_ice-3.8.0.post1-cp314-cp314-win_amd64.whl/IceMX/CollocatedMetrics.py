# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceMX.ChildInvocationMetrics import ChildInvocationMetrics

from IceMX.ChildInvocationMetrics_forward import _IceMX_ChildInvocationMetrics_t

from IceMX.CollocatedMetrics_forward import _IceMX_CollocatedMetrics_t

from dataclasses import dataclass

@dataclass(eq=False)
class CollocatedMetrics(ChildInvocationMetrics):
    """
    Provides information on invocations that are collocated. Collocated metrics are embedded within
    :class:`IceMX.InvocationMetrics`.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceMX::CollocatedMetrics``.
    """

    @staticmethod
    def ice_staticId() -> str:
        return "::IceMX::CollocatedMetrics"

_IceMX_CollocatedMetrics_t = IcePy.defineValue(
    "::IceMX::CollocatedMetrics",
    CollocatedMetrics,
    -1,
    (),
    False,
    _IceMX_ChildInvocationMetrics_t,
    ())

setattr(CollocatedMetrics, '_ice_type', _IceMX_CollocatedMetrics_t)

__all__ = ["CollocatedMetrics", "_IceMX_CollocatedMetrics_t"]
