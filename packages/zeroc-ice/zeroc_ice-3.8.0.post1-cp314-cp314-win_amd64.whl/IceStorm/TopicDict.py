# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceStorm.Topic_forward import _IceStorm_TopicPrx_t

_IceStorm_TopicDict_t = IcePy.defineDictionary("::IceStorm::TopicDict", (), IcePy._t_string, _IceStorm_TopicPrx_t)

__all__ = ["_IceStorm_TopicDict_t"]
