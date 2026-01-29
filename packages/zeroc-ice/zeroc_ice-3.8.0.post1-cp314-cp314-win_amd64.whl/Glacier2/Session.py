# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Glacier2.Session_forward import _Glacier2_SessionPrx_t

from Ice.Object import Object

from Ice.ObjectPrx import ObjectPrx
from Ice.ObjectPrx import checkedCast
from Ice.ObjectPrx import checkedCastAsync
from Ice.ObjectPrx import uncheckedCast

from Ice.OperationMode import OperationMode

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from collections.abc import Awaitable
    from collections.abc import Sequence


class SessionPrx(ObjectPrx):
    """
    Represents a session between a client application and the Glacier2 router. With Glacier2, the lifetime of a
    session is tied to the Ice connection between the client and the router: the session is destroyed when the
    connection is closed.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::Glacier2::Session``.
    
    See Also
    --------
        :class:`Glacier2.RouterPrx`
        :class:`Glacier2.SessionManagerPrx`
    """

    def destroy(self, context: dict[str, str] | None = None) -> None:
        """
        Destroys this session.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        """
        return Session._op_destroy.invoke(self, ((), context))

    def destroyAsync(self, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Destroys this session.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Session._op_destroy.invokeAsync(self, ((), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> SessionPrx | None:
        return checkedCast(SessionPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[SessionPrx | None ]:
        return checkedCastAsync(SessionPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> SessionPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> SessionPrx | None:
        return uncheckedCast(SessionPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::Glacier2::Session"

IcePy.defineProxy("::Glacier2::Session", SessionPrx)

class Session(Object, ABC):
    """
    Represents a session between a client application and the Glacier2 router. With Glacier2, the lifetime of a
    session is tied to the Ice connection between the client and the router: the session is destroyed when the
    connection is closed.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::Glacier2::Session``.
    
    See Also
    --------
        :class:`Glacier2.RouterPrx`
        :class:`Glacier2.SessionManagerPrx`
    """

    _ice_ids: Sequence[str] = ("::Glacier2::Session", "::Ice::Object", )
    _op_destroy: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::Glacier2::Session"

    @abstractmethod
    def destroy(self, current: Current) -> None | Awaitable[None]:
        """
        Destroys this session.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

Session._op_destroy = IcePy.Operation(
    "destroy",
    "destroy",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    None,
    ())

__all__ = ["Session", "SessionPrx", "_Glacier2_SessionPrx_t"]
