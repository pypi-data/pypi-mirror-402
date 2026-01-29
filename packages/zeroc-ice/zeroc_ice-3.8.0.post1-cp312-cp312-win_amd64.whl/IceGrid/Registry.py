# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.Object import Object

from Ice.ObjectPrx import ObjectPrx
from Ice.ObjectPrx import checkedCast
from Ice.ObjectPrx import checkedCastAsync
from Ice.ObjectPrx import uncheckedCast

from Ice.OperationMode import OperationMode

from IceGrid.AdminSession_forward import _IceGrid_AdminSessionPrx_t

from IceGrid.PermissionDeniedException import _IceGrid_PermissionDeniedException_t

from IceGrid.Registry_forward import _IceGrid_RegistryPrx_t

from IceGrid.Session_forward import _IceGrid_SessionPrx_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from IceGrid.AdminSession import AdminSessionPrx
    from IceGrid.Session import SessionPrx
    from collections.abc import Awaitable
    from collections.abc import Sequence


class RegistryPrx(ObjectPrx):
    """
    Represents the main entry point into the IceGrid registry service. It provides operations to create sessions
    with the registry.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::IceGrid::Registry``.
    """

    def createSession(self, userId: str, password: str, context: dict[str, str] | None = None) -> SessionPrx | None:
        """
        Creates a client session.
        
        Parameters
        ----------
        userId : str
            The user ID.
        password : str
            The password for the given user.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        SessionPrx | None
            A proxy to the newly created session. This proxy is never null.
        
        Raises
        ------
        PermissionDeniedException
            Thrown when authentication or authorization fails.
        """
        return Registry._op_createSession.invoke(self, ((userId, password), context))

    def createSessionAsync(self, userId: str, password: str, context: dict[str, str] | None = None) -> Awaitable[SessionPrx | None]:
        """
        Creates a client session.
        
        Parameters
        ----------
        userId : str
            The user ID.
        password : str
            The password for the given user.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[SessionPrx | None]
            A proxy to the newly created session. This proxy is never null.
        """
        return Registry._op_createSession.invokeAsync(self, ((userId, password), context))

    def createAdminSession(self, userId: str, password: str, context: dict[str, str] | None = None) -> AdminSessionPrx | None:
        """
        Creates an administrative session.
        
        Parameters
        ----------
        userId : str
            The user ID.
        password : str
            The password for the given user.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        AdminSessionPrx | None
            A proxy to the newly created session. This proxy is never null.
        
        Raises
        ------
        PermissionDeniedException
            Thrown when authentication or authorization fails.
        """
        return Registry._op_createAdminSession.invoke(self, ((userId, password), context))

    def createAdminSessionAsync(self, userId: str, password: str, context: dict[str, str] | None = None) -> Awaitable[AdminSessionPrx | None]:
        """
        Creates an administrative session.
        
        Parameters
        ----------
        userId : str
            The user ID.
        password : str
            The password for the given user.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[AdminSessionPrx | None]
            A proxy to the newly created session. This proxy is never null.
        """
        return Registry._op_createAdminSession.invokeAsync(self, ((userId, password), context))

    def createSessionFromSecureConnection(self, context: dict[str, str] | None = None) -> SessionPrx | None:
        """
        Creates a client session from a secure connection.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        SessionPrx | None
            A proxy to the newly created session. This proxy is never null.
        
        Raises
        ------
        PermissionDeniedException
            Thrown when authentication or authorization fails.
        """
        return Registry._op_createSessionFromSecureConnection.invoke(self, ((), context))

    def createSessionFromSecureConnectionAsync(self, context: dict[str, str] | None = None) -> Awaitable[SessionPrx | None]:
        """
        Creates a client session from a secure connection.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[SessionPrx | None]
            A proxy to the newly created session. This proxy is never null.
        """
        return Registry._op_createSessionFromSecureConnection.invokeAsync(self, ((), context))

    def createAdminSessionFromSecureConnection(self, context: dict[str, str] | None = None) -> AdminSessionPrx | None:
        """
        Creates an administrative session from a secure connection.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        AdminSessionPrx | None
            A proxy to the newly created session. This proxy is never null.
        
        Raises
        ------
        PermissionDeniedException
            Thrown when authentication or authorization fails.
        """
        return Registry._op_createAdminSessionFromSecureConnection.invoke(self, ((), context))

    def createAdminSessionFromSecureConnectionAsync(self, context: dict[str, str] | None = None) -> Awaitable[AdminSessionPrx | None]:
        """
        Creates an administrative session from a secure connection.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[AdminSessionPrx | None]
            A proxy to the newly created session. This proxy is never null.
        """
        return Registry._op_createAdminSessionFromSecureConnection.invokeAsync(self, ((), context))

    def getSessionTimeout(self, context: dict[str, str] | None = None) -> int:
        """
        Gets the session timeout. An Ice 3.7 or earlier client can use this value to determine how often it needs to
        send heartbeats (using ACM) or call :meth:`IceGrid.SessionPrx.keepAliveAsync` (resp. :meth:`IceGrid.AdminSessionPrx.keepAliveAsync`) to keep
        a session alive in the IceGrid registry.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        int
            The session timeout (in seconds).
        """
        return Registry._op_getSessionTimeout.invoke(self, ((), context))

    def getSessionTimeoutAsync(self, context: dict[str, str] | None = None) -> Awaitable[int]:
        """
        Gets the session timeout. An Ice 3.7 or earlier client can use this value to determine how often it needs to
        send heartbeats (using ACM) or call :meth:`IceGrid.SessionPrx.keepAliveAsync` (resp. :meth:`IceGrid.AdminSessionPrx.keepAliveAsync`) to keep
        a session alive in the IceGrid registry.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[int]
            The session timeout (in seconds).
        """
        return Registry._op_getSessionTimeout.invokeAsync(self, ((), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> RegistryPrx | None:
        return checkedCast(RegistryPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[RegistryPrx | None ]:
        return checkedCastAsync(RegistryPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> RegistryPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> RegistryPrx | None:
        return uncheckedCast(RegistryPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::Registry"

IcePy.defineProxy("::IceGrid::Registry", RegistryPrx)

class Registry(Object, ABC):
    """
    Represents the main entry point into the IceGrid registry service. It provides operations to create sessions
    with the registry.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::IceGrid::Registry``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::IceGrid::Registry", )
    _op_createSession: IcePy.Operation
    _op_createAdminSession: IcePy.Operation
    _op_createSessionFromSecureConnection: IcePy.Operation
    _op_createAdminSessionFromSecureConnection: IcePy.Operation
    _op_getSessionTimeout: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::Registry"

    @abstractmethod
    def createSession(self, userId: str, password: str, current: Current) -> SessionPrx | None | Awaitable[SessionPrx | None]:
        """
        Creates a client session.
        
        Parameters
        ----------
        userId : str
            The user ID.
        password : str
            The password for the given user.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        SessionPrx | None | Awaitable[SessionPrx | None]
            A proxy to the newly created session. This proxy is never null.
        
        Raises
        ------
        PermissionDeniedException
            Thrown when authentication or authorization fails.
        """
        pass

    @abstractmethod
    def createAdminSession(self, userId: str, password: str, current: Current) -> AdminSessionPrx | None | Awaitable[AdminSessionPrx | None]:
        """
        Creates an administrative session.
        
        Parameters
        ----------
        userId : str
            The user ID.
        password : str
            The password for the given user.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        AdminSessionPrx | None | Awaitable[AdminSessionPrx | None]
            A proxy to the newly created session. This proxy is never null.
        
        Raises
        ------
        PermissionDeniedException
            Thrown when authentication or authorization fails.
        """
        pass

    @abstractmethod
    def createSessionFromSecureConnection(self, current: Current) -> SessionPrx | None | Awaitable[SessionPrx | None]:
        """
        Creates a client session from a secure connection.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        SessionPrx | None | Awaitable[SessionPrx | None]
            A proxy to the newly created session. This proxy is never null.
        
        Raises
        ------
        PermissionDeniedException
            Thrown when authentication or authorization fails.
        """
        pass

    @abstractmethod
    def createAdminSessionFromSecureConnection(self, current: Current) -> AdminSessionPrx | None | Awaitable[AdminSessionPrx | None]:
        """
        Creates an administrative session from a secure connection.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        AdminSessionPrx | None | Awaitable[AdminSessionPrx | None]
            A proxy to the newly created session. This proxy is never null.
        
        Raises
        ------
        PermissionDeniedException
            Thrown when authentication or authorization fails.
        """
        pass

    @abstractmethod
    def getSessionTimeout(self, current: Current) -> int | Awaitable[int]:
        """
        Gets the session timeout. An Ice 3.7 or earlier client can use this value to determine how often it needs to
        send heartbeats (using ACM) or call :meth:`IceGrid.SessionPrx.keepAliveAsync` (resp. :meth:`IceGrid.AdminSessionPrx.keepAliveAsync`) to keep
        a session alive in the IceGrid registry.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        int | Awaitable[int]
            The session timeout (in seconds).
        """
        pass

Registry._op_createSession = IcePy.Operation(
    "createSession",
    "createSession",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0)),
    (),
    ((), _IceGrid_SessionPrx_t, False, 0),
    (_IceGrid_PermissionDeniedException_t,))

Registry._op_createAdminSession = IcePy.Operation(
    "createAdminSession",
    "createAdminSession",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0)),
    (),
    ((), _IceGrid_AdminSessionPrx_t, False, 0),
    (_IceGrid_PermissionDeniedException_t,))

Registry._op_createSessionFromSecureConnection = IcePy.Operation(
    "createSessionFromSecureConnection",
    "createSessionFromSecureConnection",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    ((), _IceGrid_SessionPrx_t, False, 0),
    (_IceGrid_PermissionDeniedException_t,))

Registry._op_createAdminSessionFromSecureConnection = IcePy.Operation(
    "createAdminSessionFromSecureConnection",
    "createAdminSessionFromSecureConnection",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    ((), _IceGrid_AdminSessionPrx_t, False, 0),
    (_IceGrid_PermissionDeniedException_t,))

Registry._op_getSessionTimeout = IcePy.Operation(
    "getSessionTimeout",
    "getSessionTimeout",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), IcePy._t_int, False, 0),
    ())
Registry._op_getSessionTimeout.deprecate("")

__all__ = ["Registry", "RegistryPrx", "_IceGrid_RegistryPrx_t"]
