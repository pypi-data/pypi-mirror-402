# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceMX.Metrics import Metrics

from IceMX.Metrics_forward import _IceMX_Metrics_t

from IceMX.SubscriberMetrics_forward import _IceMX_SubscriberMetrics_t

from dataclasses import dataclass

@dataclass(eq=False)
class SubscriberMetrics(Metrics):
    """
    Provides information about IceStorm subscribers.
    
    Attributes
    ----------
    queued : int
        The number of queued events.
    outstanding : int
        The number of outstanding events.
    delivered : int
        The number of forwarded events.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceMX::SubscriberMetrics``.
    """
    queued: int = 0
    outstanding: int = 0
    delivered: int = 0

    @staticmethod
    def ice_staticId() -> str:
        return "::IceMX::SubscriberMetrics"

_IceMX_SubscriberMetrics_t = IcePy.defineValue(
    "::IceMX::SubscriberMetrics",
    SubscriberMetrics,
    -1,
    (),
    False,
    _IceMX_Metrics_t,
    (
        ("queued", (), IcePy._t_int, False, 0),
        ("outstanding", (), IcePy._t_int, False, 0),
        ("delivered", (), IcePy._t_long, False, 0)
    ))

setattr(SubscriberMetrics, '_ice_type', _IceMX_SubscriberMetrics_t)

__all__ = ["SubscriberMetrics", "_IceMX_SubscriberMetrics_t"]
