# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from enum import Enum

class ServerState(Enum):
    """
    Represents the state of a server.
    
    Notes
    -----
        The Slice compiler generated this enum class from Slice enumeration ``::IceGrid::ServerState``.
    """

    Inactive = 0
    """
    The server is not running.
    """

    Activating = 1
    """
    The server is being activated and will change to the active state when the registered server object adapters
    are activated or to the activation timed out state if the activation timeout expires.
    """

    ActivationTimedOut = 2
    """
    The server activation timed out.
    """

    Active = 3
    """
    The server is running.
    """

    Deactivating = 4
    """
    The server is being deactivated.
    """

    Destroying = 5
    """
    The server is being destroyed.
    """

    Destroyed = 6
    """
    The server is destroyed.
    """

_IceGrid_ServerState_t = IcePy.defineEnum(
    "::IceGrid::ServerState",
    ServerState,
    (),
    {
        0: ServerState.Inactive,
        1: ServerState.Activating,
        2: ServerState.ActivationTimedOut,
        3: ServerState.Active,
        4: ServerState.Deactivating,
        5: ServerState.Destroying,
        6: ServerState.Destroyed,
    }
)

__all__ = ["ServerState", "_IceGrid_ServerState_t"]
