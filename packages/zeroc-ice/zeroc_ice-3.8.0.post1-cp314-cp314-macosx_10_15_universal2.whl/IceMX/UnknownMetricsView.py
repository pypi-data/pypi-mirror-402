# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class UnknownMetricsView(UserException):
    """
    The exception that is thrown when a metrics view cannot be found.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceMX::UnknownMetricsView``.
    """

    _ice_id = "::IceMX::UnknownMetricsView"

_IceMX_UnknownMetricsView_t = IcePy.defineException(
    "::IceMX::UnknownMetricsView",
    UnknownMetricsView,
    (),
    None,
    ())

setattr(UnknownMetricsView, '_ice_type', _IceMX_UnknownMetricsView_t)

__all__ = ["UnknownMetricsView", "_IceMX_UnknownMetricsView_t"]
