# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceMX.ConnectionMetrics_forward import _IceMX_ConnectionMetrics_t

from IceMX.Metrics import Metrics

from IceMX.Metrics_forward import _IceMX_Metrics_t

from dataclasses import dataclass

@dataclass(eq=False)
class ConnectionMetrics(Metrics):
    """
    Provides information on the data sent and received over Ice connections.
    
    Attributes
    ----------
    receivedBytes : int
        The number of bytes received by the connection.
    sentBytes : int
        The number of bytes sent by the connection.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceMX::ConnectionMetrics``.
    """
    receivedBytes: int = 0
    sentBytes: int = 0

    @staticmethod
    def ice_staticId() -> str:
        return "::IceMX::ConnectionMetrics"

_IceMX_ConnectionMetrics_t = IcePy.defineValue(
    "::IceMX::ConnectionMetrics",
    ConnectionMetrics,
    -1,
    (),
    False,
    _IceMX_Metrics_t,
    (
        ("receivedBytes", (), IcePy._t_long, False, 0),
        ("sentBytes", (), IcePy._t_long, False, 0)
    ))

setattr(ConnectionMetrics, '_ice_type', _IceMX_ConnectionMetrics_t)

__all__ = ["ConnectionMetrics", "_IceMX_ConnectionMetrics_t"]
