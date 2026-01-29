# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.Value_forward import _Ice_Value_t

_Ice_ObjectSeq_t = IcePy.defineSequence("::Ice::ObjectSeq", (), _Ice_Value_t)

__all__ = ["_Ice_ObjectSeq_t"]
