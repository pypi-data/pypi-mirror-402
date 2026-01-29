# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.LogMessage import _Ice_LogMessage_t

_Ice_LogMessageSeq_t = IcePy.defineSequence("::Ice::LogMessageSeq", (), _Ice_LogMessage_t)

__all__ = ["_Ice_LogMessageSeq_t"]
