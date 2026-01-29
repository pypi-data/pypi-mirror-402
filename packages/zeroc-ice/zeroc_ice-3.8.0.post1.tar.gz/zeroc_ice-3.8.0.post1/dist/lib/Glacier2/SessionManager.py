# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Glacier2.CannotCreateSessionException import _Glacier2_CannotCreateSessionException_t

from Glacier2.SessionControl_forward import _Glacier2_SessionControlPrx_t

from Glacier2.SessionManager_forward import _Glacier2_SessionManagerPrx_t

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
    from Glacier2.Session import SessionPrx
    from Glacier2.SessionControl import SessionControlPrx
    from Ice.Current import Current
    from collections.abc import Awaitable
    from collections.abc import Sequence


class SessionManagerPrx(ObjectPrx):
    """
    Represents an application-provided factory for session objects. You can configure a Glacier2 router with your
    own SessionManager implementation; this router will then return the sessions created by this session manager to
    its clients.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::Glacier2::SessionManager``.
    """

    def create(self, userId: str, control: SessionControlPrx | None, context: dict[str, str] | None = None) -> SessionPrx | None:
        """
        Creates a new session object.
        
        Parameters
        ----------
        userId : str
            The user ID for the session.
        control : SessionControlPrx | None
            A proxy to the session control object. This proxy is null when ``Glacier2.Server.Endpoints``
            is not configured.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        SessionPrx | None
            A proxy to the newly created session. This proxy is never null.
        
        Raises
        ------
        CannotCreateSessionException
            Thrown when the session cannot be created.
        """
        return SessionManager._op_create.invoke(self, ((userId, control), context))

    def createAsync(self, userId: str, control: SessionControlPrx | None, context: dict[str, str] | None = None) -> Awaitable[SessionPrx | None]:
        """
        Creates a new session object.
        
        Parameters
        ----------
        userId : str
            The user ID for the session.
        control : SessionControlPrx | None
            A proxy to the session control object. This proxy is null when ``Glacier2.Server.Endpoints``
            is not configured.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[SessionPrx | None]
            A proxy to the newly created session. This proxy is never null.
        """
        return SessionManager._op_create.invokeAsync(self, ((userId, control), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> SessionManagerPrx | None:
        return checkedCast(SessionManagerPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[SessionManagerPrx | None ]:
        return checkedCastAsync(SessionManagerPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> SessionManagerPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> SessionManagerPrx | None:
        return uncheckedCast(SessionManagerPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::Glacier2::SessionManager"

IcePy.defineProxy("::Glacier2::SessionManager", SessionManagerPrx)

class SessionManager(Object, ABC):
    """
    Represents an application-provided factory for session objects. You can configure a Glacier2 router with your
    own SessionManager implementation; this router will then return the sessions created by this session manager to
    its clients.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::Glacier2::SessionManager``.
    """

    _ice_ids: Sequence[str] = ("::Glacier2::SessionManager", "::Ice::Object", )
    _op_create: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::Glacier2::SessionManager"

    @abstractmethod
    def create(self, userId: str, control: SessionControlPrx | None, current: Current) -> SessionPrx | None | Awaitable[SessionPrx | None]:
        """
        Creates a new session object.
        
        Parameters
        ----------
        userId : str
            The user ID for the session.
        control : SessionControlPrx | None
            A proxy to the session control object. This proxy is null when ``Glacier2.Server.Endpoints``
            is not configured.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        SessionPrx | None | Awaitable[SessionPrx | None]
            A proxy to the newly created session. This proxy is never null.
        
        Raises
        ------
        CannotCreateSessionException
            Thrown when the session cannot be created.
        """
        pass

SessionManager._op_create = IcePy.Operation(
    "create",
    "create",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), _Glacier2_SessionControlPrx_t, False, 0)),
    (),
    ((), _Glacier2_SessionPrx_t, False, 0),
    (_Glacier2_CannotCreateSessionException_t,))

__all__ = ["SessionManager", "SessionManagerPrx", "_Glacier2_SessionManagerPrx_t"]
