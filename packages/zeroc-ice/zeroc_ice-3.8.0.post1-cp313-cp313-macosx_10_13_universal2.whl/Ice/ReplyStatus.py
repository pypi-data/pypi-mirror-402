# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from enum import Enum

class ReplyStatus(Enum):
    """
    Represents the status of a reply.
    A reply status can have any value in the range 0..255. Do not use this enum to marshal or unmarshal a reply
    status unless you know its value corresponds to one of the enumerators defined below.
    
    Notes
    -----
        The Slice compiler generated this enum class from Slice enumeration ``::Ice::ReplyStatus``.
    """

    Ok = 0
    """
    The dispatch completed successfully.
    """

    UserException = 1
    """
    The dispatch completed with a Slice user exception.
    """

    ObjectNotExist = 2
    """
    The dispatch could not find an implementation for the target object.
    """

    FacetNotExist = 3
    """
    The dispatch found an implementation for the target object but could not find the requested facet.
    """

    OperationNotExist = 4
    """
    The dispatch found an implementation for the target object but could not find the requested operation.
    """

    UnknownLocalException = 5
    """
    The dispatch failed with an Ice local exception.
    """

    UnknownUserException = 6
    """
    The dispatch failed with a Slice user exception that does not conform to the exception specification of
    the operation.
    """

    UnknownException = 7
    """
    The dispatch failed with some other exception (neither an Ice local exception nor a Slice user exception).
    """

    InvalidData = 8
    """
    The dispatch failed because the request payload could not be unmarshaled. It is typically due to a mismatch
    in the Slice definitions used by the client and the server.
    """

    Unauthorized = 9
    """
    The caller is not authorized to access the requested resource.
    """

_Ice_ReplyStatus_t = IcePy.defineEnum(
    "::Ice::ReplyStatus",
    ReplyStatus,
    (),
    {
        0: ReplyStatus.Ok,
        1: ReplyStatus.UserException,
        2: ReplyStatus.ObjectNotExist,
        3: ReplyStatus.FacetNotExist,
        4: ReplyStatus.OperationNotExist,
        5: ReplyStatus.UnknownLocalException,
        6: ReplyStatus.UnknownUserException,
        7: ReplyStatus.UnknownException,
        8: ReplyStatus.InvalidData,
        9: ReplyStatus.Unauthorized,
    }
)

__all__ = ["ReplyStatus", "_Ice_ReplyStatus_t"]
