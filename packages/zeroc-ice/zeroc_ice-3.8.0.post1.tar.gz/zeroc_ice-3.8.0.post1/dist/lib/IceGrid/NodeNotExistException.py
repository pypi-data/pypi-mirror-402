# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.UserException import UserException

from dataclasses import dataclass


@dataclass
class NodeNotExistException(UserException):
    """
    The exception that is thrown when IceGrid does not know a node with the provided name.
    
    Attributes
    ----------
    name : str
        The node name.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceGrid::NodeNotExistException``.
    """
    name: str = ""

    _ice_id = "::IceGrid::NodeNotExistException"

_IceGrid_NodeNotExistException_t = IcePy.defineException(
    "::IceGrid::NodeNotExistException",
    NodeNotExistException,
    (),
    None,
    (("name", (), IcePy._t_string, False, 0),))

setattr(NodeNotExistException, '_ice_type', _IceGrid_NodeNotExistException_t)

__all__ = ["NodeNotExistException", "_IceGrid_NodeNotExistException_t"]
