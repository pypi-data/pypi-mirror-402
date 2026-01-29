# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.Value import Value

from IceMX.Metrics_forward import _IceMX_Metrics_t

from dataclasses import dataclass

@dataclass(eq=False)
class Metrics(Value):
    """
    The base class for metrics. A metrics object represents a collection of measurements associated to a given a
    system.
    
    Attributes
    ----------
    id : str
        The metrics identifier.
    total : int
        The total number of objects observed by this metrics. This includes the number of currently observed objects
        and the number of objects observed in the past.
    current : int
        The number of objects currently observed by this metrics.
    totalLifetime : int
        The sum of the lifetime of each observed objects. This does not include the lifetime of objects which are
        currently observed, only the objects observed in the past.
    failures : int
        The number of failures observed.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceMX::Metrics``.
    """
    id: str = ""
    total: int = 0
    current: int = 0
    totalLifetime: int = 0
    failures: int = 0

    @staticmethod
    def ice_staticId() -> str:
        return "::IceMX::Metrics"

_IceMX_Metrics_t = IcePy.defineValue(
    "::IceMX::Metrics",
    Metrics,
    -1,
    (),
    False,
    None,
    (
        ("id", (), IcePy._t_string, False, 0),
        ("total", (), IcePy._t_long, False, 0),
        ("current", (), IcePy._t_int, False, 0),
        ("totalLifetime", (), IcePy._t_long, False, 0),
        ("failures", (), IcePy._t_int, False, 0)
    ))

setattr(Metrics, '_ice_type', _IceMX_Metrics_t)

__all__ = ["Metrics", "_IceMX_Metrics_t"]
