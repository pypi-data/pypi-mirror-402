# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceMX.Metrics import Metrics

from IceMX.Metrics_forward import _IceMX_Metrics_t

from IceMX.SessionMetrics_forward import _IceMX_SessionMetrics_t

from dataclasses import dataclass

@dataclass(eq=False)
class SessionMetrics(Metrics):
    """
    Provides information about Glacier2 sessions.
    
    Attributes
    ----------
    forwardedClient : int
        The number of client requests forwarded.
    forwardedServer : int
        The number of server requests forwarded.
    routingTableSize : int
        The size of the routing table.
    queuedClient : int
        The number of client requests queued.
    queuedServer : int
        The number of server requests queued.
    overriddenClient : int
        The number of client requests overridden.
    overriddenServer : int
        The number of server requests overridden.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceMX::SessionMetrics``.
    """
    forwardedClient: int = 0
    forwardedServer: int = 0
    routingTableSize: int = 0
    queuedClient: int = 0
    queuedServer: int = 0
    overriddenClient: int = 0
    overriddenServer: int = 0

    @staticmethod
    def ice_staticId() -> str:
        return "::IceMX::SessionMetrics"

_IceMX_SessionMetrics_t = IcePy.defineValue(
    "::IceMX::SessionMetrics",
    SessionMetrics,
    -1,
    (),
    False,
    _IceMX_Metrics_t,
    (
        ("forwardedClient", (), IcePy._t_int, False, 0),
        ("forwardedServer", (), IcePy._t_int, False, 0),
        ("routingTableSize", (), IcePy._t_int, False, 0),
        ("queuedClient", (), IcePy._t_int, False, 0),
        ("queuedServer", (), IcePy._t_int, False, 0),
        ("overriddenClient", (), IcePy._t_int, False, 0),
        ("overriddenServer", (), IcePy._t_int, False, 0)
    ))

setattr(SessionMetrics, '_ice_type', _IceMX_SessionMetrics_t)

__all__ = ["SessionMetrics", "_IceMX_SessionMetrics_t"]
