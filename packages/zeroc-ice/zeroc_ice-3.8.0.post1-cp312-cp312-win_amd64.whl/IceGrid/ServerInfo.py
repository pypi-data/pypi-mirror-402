# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceGrid.ServerDescriptor_forward import _IceGrid_ServerDescriptor_t

from dataclasses import dataclass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IceGrid.ServerDescriptor import ServerDescriptor


@dataclass
class ServerInfo:
    """
    Information about a server managed by an IceGrid node.
    
    Attributes
    ----------
    application : str
        The application to which this server belongs.
    uuid : str
        The application UUID.
    revision : int
        The application revision.
    node : str
        The IceGrid node where this server is deployed.
    descriptor : ServerDescriptor | None
        The server descriptor.
    sessionId : str
        The ID of the session which allocated the server.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::ServerInfo``.
    """
    application: str = ""
    uuid: str = ""
    revision: int = 0
    node: str = ""
    descriptor: ServerDescriptor | None = None
    sessionId: str = ""

_IceGrid_ServerInfo_t = IcePy.defineStruct(
    "::IceGrid::ServerInfo",
    ServerInfo,
    (),
    (
        ("application", (), IcePy._t_string),
        ("uuid", (), IcePy._t_string),
        ("revision", (), IcePy._t_int),
        ("node", (), IcePy._t_string),
        ("descriptor", (), _IceGrid_ServerDescriptor_t),
        ("sessionId", (), IcePy._t_string)
    ))

__all__ = ["ServerInfo", "_IceGrid_ServerInfo_t"]
