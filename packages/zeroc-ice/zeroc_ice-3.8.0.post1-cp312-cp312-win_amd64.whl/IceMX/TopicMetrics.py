# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceMX.Metrics import Metrics

from IceMX.Metrics_forward import _IceMX_Metrics_t

from IceMX.TopicMetrics_forward import _IceMX_TopicMetrics_t

from dataclasses import dataclass

@dataclass(eq=False)
class TopicMetrics(Metrics):
    """
    Provides information about one or more IceStorm topics.
    
    Attributes
    ----------
    published : int
        The number of events published on the topic(s) by publishers.
    forwarded : int
        The number of events forwarded on the topic(s) by IceStorm topic links.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceMX::TopicMetrics``.
    """
    published: int = 0
    forwarded: int = 0

    @staticmethod
    def ice_staticId() -> str:
        return "::IceMX::TopicMetrics"

_IceMX_TopicMetrics_t = IcePy.defineValue(
    "::IceMX::TopicMetrics",
    TopicMetrics,
    -1,
    (),
    False,
    _IceMX_Metrics_t,
    (
        ("published", (), IcePy._t_long, False, 0),
        ("forwarded", (), IcePy._t_long, False, 0)
    ))

setattr(TopicMetrics, '_ice_type', _IceMX_TopicMetrics_t)

__all__ = ["TopicMetrics", "_IceMX_TopicMetrics_t"]
