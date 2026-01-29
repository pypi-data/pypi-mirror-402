# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.Value import Value

from IceGrid.BoxedString_forward import _IceGrid_BoxedString_t

from dataclasses import dataclass

@dataclass(eq=False)
class BoxedString(Value):
    """
    A "boxed" string.
    
    Attributes
    ----------
    value : str
        The value of the boxed string.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceGrid::BoxedString``.
    """
    value: str = ""

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::BoxedString"

_IceGrid_BoxedString_t = IcePy.defineValue(
    "::IceGrid::BoxedString",
    BoxedString,
    -1,
    (),
    False,
    None,
    (("value", (), IcePy._t_string, False, 0),))

setattr(BoxedString, '_ice_type', _IceGrid_BoxedString_t)

__all__ = ["BoxedString", "_IceGrid_BoxedString_t"]
