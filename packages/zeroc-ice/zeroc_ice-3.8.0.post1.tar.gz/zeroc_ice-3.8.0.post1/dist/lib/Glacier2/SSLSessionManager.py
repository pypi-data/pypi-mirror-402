# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Glacier2.CannotCreateSessionException import _Glacier2_CannotCreateSessionException_t

from Glacier2.SSLInfo import _Glacier2_SSLInfo_t

from Glacier2.SSLSessionManager_forward import _Glacier2_SSLSessionManagerPrx_t

from Glacier2.SessionControl_forward import _Glacier2_SessionControlPrx_t

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
    from Glacier2.SSLInfo import SSLInfo
    from Glacier2.Session import SessionPrx
    from Glacier2.SessionControl import SessionControlPrx
    from Ice.Current import Current
    from collections.abc import Awaitable
    from collections.abc import Sequence


class SSLSessionManagerPrx(ObjectPrx):
    """
    Represents an application-provided factory for session objects. You can configure a Glacier2 router with your
    own SSLSessionManager implementation; this router will then return the sessions created by this session manager
    to its clients.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::Glacier2::SSLSessionManager``.
    """

    def create(self, info: SSLInfo, control: SessionControlPrx | None, context: dict[str, str] | None = None) -> SessionPrx | None:
        """
        Creates a new session object.
        
        Parameters
        ----------
        info : SSLInfo
            The SSL info.
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
        return SSLSessionManager._op_create.invoke(self, ((info, control), context))

    def createAsync(self, info: SSLInfo, control: SessionControlPrx | None, context: dict[str, str] | None = None) -> Awaitable[SessionPrx | None]:
        """
        Creates a new session object.
        
        Parameters
        ----------
        info : SSLInfo
            The SSL info.
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
        return SSLSessionManager._op_create.invokeAsync(self, ((info, control), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> SSLSessionManagerPrx | None:
        return checkedCast(SSLSessionManagerPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[SSLSessionManagerPrx | None ]:
        return checkedCastAsync(SSLSessionManagerPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> SSLSessionManagerPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> SSLSessionManagerPrx | None:
        return uncheckedCast(SSLSessionManagerPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::Glacier2::SSLSessionManager"

IcePy.defineProxy("::Glacier2::SSLSessionManager", SSLSessionManagerPrx)

class SSLSessionManager(Object, ABC):
    """
    Represents an application-provided factory for session objects. You can configure a Glacier2 router with your
    own SSLSessionManager implementation; this router will then return the sessions created by this session manager
    to its clients.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::Glacier2::SSLSessionManager``.
    """

    _ice_ids: Sequence[str] = ("::Glacier2::SSLSessionManager", "::Ice::Object", )
    _op_create: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::Glacier2::SSLSessionManager"

    @abstractmethod
    def create(self, info: SSLInfo, control: SessionControlPrx | None, current: Current) -> SessionPrx | None | Awaitable[SessionPrx | None]:
        """
        Creates a new session object.
        
        Parameters
        ----------
        info : SSLInfo
            The SSL info.
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

SSLSessionManager._op_create = IcePy.Operation(
    "create",
    "create",
    OperationMode.Normal,
    None,
    (),
    (((), _Glacier2_SSLInfo_t, False, 0), ((), _Glacier2_SessionControlPrx_t, False, 0)),
    (),
    ((), _Glacier2_SessionPrx_t, False, 0),
    (_Glacier2_CannotCreateSessionException_t,))

__all__ = ["SSLSessionManager", "SSLSessionManagerPrx", "_Glacier2_SSLSessionManagerPrx_t"]
