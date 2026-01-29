# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceMX.StringIntDict import _IceMX_StringIntDict_t

from dataclasses import dataclass
from dataclasses import field


@dataclass
class MetricsFailures:
    """
    Keeps track of metrics failures.
    
    Attributes
    ----------
    id : str
        The identifier of the metrics object associated to the failures.
    failures : dict[str, int]
        The failures observed for this metrics.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceMX::MetricsFailures``.
    """
    id: str = ""
    failures: dict[str, int] = field(default_factory=dict)

_IceMX_MetricsFailures_t = IcePy.defineStruct(
    "::IceMX::MetricsFailures",
    MetricsFailures,
    (),
    (
        ("id", (), IcePy._t_string),
        ("failures", (), _IceMX_StringIntDict_t)
    ))

__all__ = ["MetricsFailures", "_IceMX_MetricsFailures_t"]
