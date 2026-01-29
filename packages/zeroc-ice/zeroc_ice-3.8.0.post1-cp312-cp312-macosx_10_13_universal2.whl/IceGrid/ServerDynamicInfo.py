# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.ServerState import ServerState
from IceGrid.ServerState import _IceGrid_ServerState_t

from dataclasses import dataclass


@dataclass(order=True, unsafe_hash=True)
class ServerDynamicInfo:
    """
    Dynamic information about the state of a server.
    
    Attributes
    ----------
    id : str
        The ID of the server.
    state : ServerState
        The state of the server.
    pid : int
        The process ID of the server.
    enabled : bool
        Indicates whether the server is enabled.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::ServerDynamicInfo``.
    """
    id: str = ""
    state: ServerState = ServerState.Inactive
    pid: int = 0
    enabled: bool = False

_IceGrid_ServerDynamicInfo_t = IcePy.defineStruct(
    "::IceGrid::ServerDynamicInfo",
    ServerDynamicInfo,
    (),
    (
        ("id", (), IcePy._t_string),
        ("state", (), _IceGrid_ServerState_t),
        ("pid", (), IcePy._t_int),
        ("enabled", (), IcePy._t_bool)
    ))

__all__ = ["ServerDynamicInfo", "_IceGrid_ServerDynamicInfo_t"]
