# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.LogMessageType import LogMessageType
from Ice.LogMessageType import _Ice_LogMessageType_t

from dataclasses import dataclass


@dataclass(order=True, unsafe_hash=True)
class LogMessage:
    """
    Represents a full log message.
    
    Attributes
    ----------
    type : LogMessageType
        The type of message sent to the :class:`Ice.RemoteLoggerPrx`.
    timestamp : int
        The date and time when the :class:`Ice.RemoteLoggerPrx` received this message, expressed as the number of
        microseconds since the Unix Epoch (00:00:00 UTC on 1 January 1970).
    traceCategory : str
        For a message of type 'trace', the trace category of this log message; otherwise, the empty string.
    message : str
        The log message itself.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::Ice::LogMessage``.
    """
    type: LogMessageType = LogMessageType.PrintMessage
    timestamp: int = 0
    traceCategory: str = ""
    message: str = ""

_Ice_LogMessage_t = IcePy.defineStruct(
    "::Ice::LogMessage",
    LogMessage,
    (),
    (
        ("type", (), _Ice_LogMessageType_t),
        ("timestamp", (), IcePy._t_long),
        ("traceCategory", (), IcePy._t_string),
        ("message", (), IcePy._t_string)
    ))

__all__ = ["LogMessage", "_Ice_LogMessage_t"]
