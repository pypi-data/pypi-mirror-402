# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.Identity import _Ice_Identity_t

_Ice_IdentitySeq_t = IcePy.defineSequence("::Ice::IdentitySeq", (), _Ice_Identity_t)

__all__ = ["_Ice_IdentitySeq_t"]
