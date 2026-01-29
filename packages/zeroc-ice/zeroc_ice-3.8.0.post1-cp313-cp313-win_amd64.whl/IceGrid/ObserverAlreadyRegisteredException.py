# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.Identity import Identity
from Ice.Identity import _Ice_Identity_t

from Ice.UserException import UserException

from dataclasses import dataclass
from dataclasses import field


@dataclass
class ObserverAlreadyRegisteredException(UserException):
    """
    The exception that is thrown when an observer is already registered with the registry.
    
    Attributes
    ----------
    id : Identity
        The identity of the observer.
    
    Notes
    -----
        The Slice compiler generated this exception dataclass from Slice exception ``::IceGrid::ObserverAlreadyRegisteredException``.
    
    See Also
    --------
        :meth:`IceGrid.AdminSessionPrx.setObserversAsync`
        :meth:`IceGrid.AdminSessionPrx.setObserversByIdentityAsync`
    """
    id: Identity = field(default_factory=Identity)

    _ice_id = "::IceGrid::ObserverAlreadyRegisteredException"

_IceGrid_ObserverAlreadyRegisteredException_t = IcePy.defineException(
    "::IceGrid::ObserverAlreadyRegisteredException",
    ObserverAlreadyRegisteredException,
    (),
    None,
    (("id", (), _Ice_Identity_t, False, 0),))

setattr(ObserverAlreadyRegisteredException, '_ice_type', _IceGrid_ObserverAlreadyRegisteredException_t)

__all__ = ["ObserverAlreadyRegisteredException", "_IceGrid_ObserverAlreadyRegisteredException_t"]
