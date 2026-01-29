# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from dataclasses import dataclass


@dataclass(order=True, unsafe_hash=True)
class NodeInfo:
    """
    Information about an IceGrid node.
    
    Attributes
    ----------
    name : str
        The name of the node.
    os : str
        The operating system name.
    hostname : str
        The network name of the host running this node.
    release : str
        The operation system release level.
    version : str
        The operation system version.
    machine : str
        The machine hardware type.
    nProcessors : int
        The number of processor threads on the node.
        For example, nProcessors is 8 on a computer with a single quad-core processor and two threads per core.
    dataDir : str
        The path to the node data directory.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceGrid::NodeInfo``.
    """
    name: str = ""
    os: str = ""
    hostname: str = ""
    release: str = ""
    version: str = ""
    machine: str = ""
    nProcessors: int = 0
    dataDir: str = ""

_IceGrid_NodeInfo_t = IcePy.defineStruct(
    "::IceGrid::NodeInfo",
    NodeInfo,
    (),
    (
        ("name", (), IcePy._t_string),
        ("os", (), IcePy._t_string),
        ("hostname", (), IcePy._t_string),
        ("release", (), IcePy._t_string),
        ("version", (), IcePy._t_string),
        ("machine", (), IcePy._t_string),
        ("nProcessors", (), IcePy._t_int),
        ("dataDir", (), IcePy._t_string)
    ))

__all__ = ["NodeInfo", "_IceGrid_NodeInfo_t"]
