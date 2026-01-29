# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceStorm.LinkInfo import _IceStorm_LinkInfo_t

_IceStorm_LinkInfoSeq_t = IcePy.defineSequence("::IceStorm::LinkInfoSeq", (), _IceStorm_LinkInfo_t)

__all__ = ["_IceStorm_LinkInfoSeq_t"]
