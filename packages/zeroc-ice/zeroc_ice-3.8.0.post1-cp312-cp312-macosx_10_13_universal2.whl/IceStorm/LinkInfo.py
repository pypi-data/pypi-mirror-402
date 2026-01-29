# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from IceStorm.Topic_forward import _IceStorm_TopicPrx_t

from dataclasses import dataclass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IceStorm.Topic import TopicPrx


@dataclass
class LinkInfo:
    """
    Information about a topic link.
    
    Attributes
    ----------
    theTopic : TopicPrx | None
        The linked topic proxy. This proxy is never null.
    name : str
        The name of the linked topic.
    cost : int
        The cost of traversing this link.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::IceStorm::LinkInfo``.
    """
    theTopic: TopicPrx | None = None
    name: str = ""
    cost: int = 0

_IceStorm_LinkInfo_t = IcePy.defineStruct(
    "::IceStorm::LinkInfo",
    LinkInfo,
    (),
    (
        ("theTopic", (), _IceStorm_TopicPrx_t),
        ("name", (), IcePy._t_string),
        ("cost", (), IcePy._t_int)
    ))

__all__ = ["LinkInfo", "_IceStorm_LinkInfo_t"]
