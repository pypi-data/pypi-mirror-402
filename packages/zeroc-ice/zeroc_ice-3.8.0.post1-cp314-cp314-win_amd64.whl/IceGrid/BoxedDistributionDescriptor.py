# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.Value import Value

from IceGrid.BoxedDistributionDescriptor_forward import _IceGrid_BoxedDistributionDescriptor_t

from IceGrid.DistributionDescriptor import DistributionDescriptor
from IceGrid.DistributionDescriptor import _IceGrid_DistributionDescriptor_t

from dataclasses import dataclass
from dataclasses import field

@dataclass(eq=False)
class BoxedDistributionDescriptor(Value):
    """
    A "boxed" distribution descriptor.
    
    Attributes
    ----------
    value : DistributionDescriptor
        The value of the boxed distribution descriptor.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceGrid::BoxedDistributionDescriptor``.
    """
    value: DistributionDescriptor = field(default_factory=DistributionDescriptor)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::BoxedDistributionDescriptor"

_IceGrid_BoxedDistributionDescriptor_t = IcePy.defineValue(
    "::IceGrid::BoxedDistributionDescriptor",
    BoxedDistributionDescriptor,
    -1,
    (),
    False,
    None,
    (("value", (), _IceGrid_DistributionDescriptor_t, False, 0),))

setattr(BoxedDistributionDescriptor, '_ice_type', _IceGrid_BoxedDistributionDescriptor_t)

__all__ = ["BoxedDistributionDescriptor", "_IceGrid_BoxedDistributionDescriptor_t"]
