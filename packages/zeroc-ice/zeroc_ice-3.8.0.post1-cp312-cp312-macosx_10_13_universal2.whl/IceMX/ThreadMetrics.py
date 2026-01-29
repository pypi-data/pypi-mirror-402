# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceMX.Metrics import Metrics

from IceMX.Metrics_forward import _IceMX_Metrics_t

from IceMX.ThreadMetrics_forward import _IceMX_ThreadMetrics_t

from dataclasses import dataclass

@dataclass(eq=False)
class ThreadMetrics(Metrics):
    """
    Provides information on the number of threads currently in use and their activity.
    
    Attributes
    ----------
    inUseForIO : int
        The number of threads which are currently performing socket reads or writes.
    inUseForUser : int
        The number of threads which are currently calling user code (servant dispatch, AMI callbacks, etc).
    inUseForOther : int
        The number of threads which are currently performing other activities such as DNS lookups, garbage
        collection, etc. These are all the other threads created by the Ice runtime that are not counted in
        :class:`IceMX.ThreadMetrics.inUseForUser` or :class:`IceMX.ThreadMetrics.inUseForIO`.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceMX::ThreadMetrics``.
    """
    inUseForIO: int = 0
    inUseForUser: int = 0
    inUseForOther: int = 0

    @staticmethod
    def ice_staticId() -> str:
        return "::IceMX::ThreadMetrics"

_IceMX_ThreadMetrics_t = IcePy.defineValue(
    "::IceMX::ThreadMetrics",
    ThreadMetrics,
    -1,
    (),
    False,
    _IceMX_Metrics_t,
    (
        ("inUseForIO", (), IcePy._t_int, False, 0),
        ("inUseForUser", (), IcePy._t_int, False, 0),
        ("inUseForOther", (), IcePy._t_int, False, 0)
    ))

setattr(ThreadMetrics, '_ice_type', _IceMX_ThreadMetrics_t)

__all__ = ["ThreadMetrics", "_IceMX_ThreadMetrics_t"]
