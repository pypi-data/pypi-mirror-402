# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from enum import Enum

class OperationMode(Enum):
    """
    Specifies if an operation is idempotent, which affects the retry behavior of the Ice client runtime.
    
    Notes
    -----
        The Slice compiler generated this enum class from Slice enumeration ``::Ice::OperationMode``.
    """

    Normal = 0
    """
    A non-idempotent operation (the default). The Ice client runtime guarantees that it will not violate
    at-most-once semantics for operations with this mode.
    """

    Nonmutating = 1
    """
    Equivalent to :class:`Ice.OperationMode.Idempotent`, but deprecated.
    """

    Idempotent = 2
    """
    An idempotent operation. The Ice client runtime does not guarantee at-most-once semantics for such an
    operation.
    
    Notes
    -----
        When an operation is idempotent, the Ice runtime will attempt to transparently recover from certain
        runtime errors by re-issuing a failed request transparently.
    """

_Ice_OperationMode_t = IcePy.defineEnum(
    "::Ice::OperationMode",
    OperationMode,
    (),
    {
        0: OperationMode.Normal,
        1: OperationMode.Nonmutating,
        2: OperationMode.Idempotent,
    }
)

__all__ = ["OperationMode", "_Ice_OperationMode_t"]
