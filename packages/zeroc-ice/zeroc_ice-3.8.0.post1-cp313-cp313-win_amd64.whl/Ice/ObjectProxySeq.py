# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.ObjectPrx_forward import _Ice_ObjectPrx_t

_Ice_ObjectProxySeq_t = IcePy.defineSequence("::Ice::ObjectProxySeq", (), _Ice_ObjectPrx_t)

__all__ = ["_Ice_ObjectProxySeq_t"]
