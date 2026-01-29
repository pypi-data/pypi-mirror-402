# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class NodeUnreachableException(UserException):
    """
    The exception that is thrown when IceGrid cannot reach a node.
    
    Attributes
    ----------
    name : str
        The name of the node that is not reachable.
    reason : str
        The reason why the node couldn't be reached.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceGrid::NodeUnreachableException``.
    """
    name: str = ""
    reason: str = ""

    _ice_id = "::IceGrid::NodeUnreachableException"

_IceGrid_NodeUnreachableException_t = IcePy.defineException(
    "::IceGrid::NodeUnreachableException",
    NodeUnreachableException,
    (),
    None,
    (
        ("name", (), IcePy._t_string, False, 0),
        ("reason", (), IcePy._t_string, False, 0)
    ))

setattr(NodeUnreachableException, '_ice_type', _IceGrid_NodeUnreachableException_t)

__all__ = ["NodeUnreachableException", "_IceGrid_NodeUnreachableException_t"]
