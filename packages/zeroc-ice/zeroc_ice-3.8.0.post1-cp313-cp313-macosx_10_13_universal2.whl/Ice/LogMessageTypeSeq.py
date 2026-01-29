# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.LogMessageType import _Ice_LogMessageType_t

_Ice_LogMessageTypeSeq_t = IcePy.defineSequence("::Ice::LogMessageTypeSeq", (), _Ice_LogMessageType_t)

__all__ = ["_Ice_LogMessageTypeSeq_t"]
