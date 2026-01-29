# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Glacier2.CannotCreateSessionException import _Glacier2_CannotCreateSessionException_t

from Glacier2.PermissionDeniedException import _Glacier2_PermissionDeniedException_t

from Glacier2.Router_forward import _Glacier2_RouterPrx_t

from Glacier2.SessionNotExistException import _Glacier2_SessionNotExistException_t

from Glacier2.Session_forward import _Glacier2_SessionPrx_t

from Ice.ObjectProxySeq import _Ice_ObjectProxySeq_t

from Ice.ObjectPrx import checkedCast
from Ice.ObjectPrx import checkedCastAsync
from Ice.ObjectPrx import uncheckedCast

from Ice.ObjectPrx_forward import _Ice_ObjectPrx_t

from Ice.OperationMode import OperationMode

from Ice.Router import Router as _m_Ice_Router_Router
from Ice.Router import RouterPrx as _m_Ice_Router_RouterPrx

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Glacier2.Session import SessionPrx
    from Ice.Current import Current
    from Ice.ObjectPrx import ObjectPrx
    from collections.abc import Awaitable
    from collections.abc import Sequence


class RouterPrx(_m_Ice_Router_RouterPrx):
    """
    The Glacier2 specialization of the :class:`Ice.RouterPrx` interface.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::Glacier2::Router``.
    """

    def getCategoryForClient(self, context: dict[str, str] | None = None) -> str:
        """
        Gets a unique category that identifies the client (caller) in the router. This category must be used in the
        identities of all the client's callback objects.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        str
            The category. It's an empty string when ``Glacier2.Server.Endpoints`` is not configured.
        """
        return Router._op_getCategoryForClient.invoke(self, ((), context))

    def getCategoryForClientAsync(self, context: dict[str, str] | None = None) -> Awaitable[str]:
        """
        Gets a unique category that identifies the client (caller) in the router. This category must be used in the
        identities of all the client's callback objects.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[str]
            The category. It's an empty string when ``Glacier2.Server.Endpoints`` is not configured.
        """
        return Router._op_getCategoryForClient.invokeAsync(self, ((), context))

    def createSession(self, userId: str, password: str, context: dict[str, str] | None = None) -> SessionPrx | None:
        """
        Creates a session for the client (caller) with the router. If a :class:`Glacier2.SessionManagerPrx` is configured,
        a proxy to a :class:`Glacier2.SessionPrx` object is returned to the client. Otherwise, null is returned and only an
        internal session (i.e., not visible to the client) is created.
        If a non-null session proxy is returned, it must be configured to route through the router that created it.
        This occurs automatically when the router is configured as the client's default router at the time the
        session proxy is created in the client application; otherwise, the client must configure the session proxy
        explicitly.
        
        Parameters
        ----------
        userId : str
            The user ID.
        password : str
            The password.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        SessionPrx | None
            A proxy for the newly created session, or null if no :class:`Glacier2.SessionManagerPrx` is configured.
        
        Raises
        ------
        CannotCreateSessionException
            Thrown when the session cannot be created.
        PermissionDeniedException
            Thrown when an authentication or authorization failure occurs.
        
        See Also
        --------
            :class:`Glacier2.SessionPrx`
            :class:`Glacier2.SessionManagerPrx`
            :class:`Glacier2.PermissionsVerifierPrx`
        """
        return Router._op_createSession.invoke(self, ((userId, password), context))

    def createSessionAsync(self, userId: str, password: str, context: dict[str, str] | None = None) -> Awaitable[SessionPrx | None]:
        """
        Creates a session for the client (caller) with the router. If a :class:`Glacier2.SessionManagerPrx` is configured,
        a proxy to a :class:`Glacier2.SessionPrx` object is returned to the client. Otherwise, null is returned and only an
        internal session (i.e., not visible to the client) is created.
        If a non-null session proxy is returned, it must be configured to route through the router that created it.
        This occurs automatically when the router is configured as the client's default router at the time the
        session proxy is created in the client application; otherwise, the client must configure the session proxy
        explicitly.
        
        Parameters
        ----------
        userId : str
            The user ID.
        password : str
            The password.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[SessionPrx | None]
            A proxy for the newly created session, or null if no :class:`Glacier2.SessionManagerPrx` is configured.
        
        See Also
        --------
            :class:`Glacier2.SessionPrx`
            :class:`Glacier2.SessionManagerPrx`
            :class:`Glacier2.PermissionsVerifierPrx`
        """
        return Router._op_createSession.invokeAsync(self, ((userId, password), context))

    def createSessionFromSecureConnection(self, context: dict[str, str] | None = None) -> SessionPrx | None:
        """
        Creates a per-client session with the router. The user is authenticated through the SSL certificate(s)
        associated with the connection. If an :class:`Glacier2.SSLSessionManagerPrx` is configured, a proxy to a :class:`Glacier2.SessionPrx`
        object is returned to the client. Otherwise, null is returned and only an internal session (i.e., not
        visible to the client) is created.
        If a non-null session proxy is returned, it must be configured to route through the router that created it.
        This occurs automatically when the router is configured as the client's default router at the time the
        session proxy is created in the client application; otherwise, the client must configure the session proxy
        explicitly.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        SessionPrx | None
            A proxy for the newly created session, or null if no :class:`Glacier2.SSLSessionManagerPrx` is configured.
        
        Raises
        ------
        CannotCreateSessionException
            Thrown when the session cannot be created.
        PermissionDeniedException
            Thrown when an authentication or authorization failure occurs.
        
        See Also
        --------
            :class:`Glacier2.SessionPrx`
            :class:`Glacier2.SessionManagerPrx`
            :class:`Glacier2.PermissionsVerifierPrx`
        """
        return Router._op_createSessionFromSecureConnection.invoke(self, ((), context))

    def createSessionFromSecureConnectionAsync(self, context: dict[str, str] | None = None) -> Awaitable[SessionPrx | None]:
        """
        Creates a per-client session with the router. The user is authenticated through the SSL certificate(s)
        associated with the connection. If an :class:`Glacier2.SSLSessionManagerPrx` is configured, a proxy to a :class:`Glacier2.SessionPrx`
        object is returned to the client. Otherwise, null is returned and only an internal session (i.e., not
        visible to the client) is created.
        If a non-null session proxy is returned, it must be configured to route through the router that created it.
        This occurs automatically when the router is configured as the client's default router at the time the
        session proxy is created in the client application; otherwise, the client must configure the session proxy
        explicitly.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[SessionPrx | None]
            A proxy for the newly created session, or null if no :class:`Glacier2.SSLSessionManagerPrx` is configured.
        
        See Also
        --------
            :class:`Glacier2.SessionPrx`
            :class:`Glacier2.SessionManagerPrx`
            :class:`Glacier2.PermissionsVerifierPrx`
        """
        return Router._op_createSessionFromSecureConnection.invokeAsync(self, ((), context))

    def refreshSession(self, context: dict[str, str] | None = None) -> None:
        """
        Keeps the session with this router alive.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        SessionNotExistException
            Thrown when no session exists for the caller (client).
        """
        return Router._op_refreshSession.invoke(self, ((), context))

    def refreshSessionAsync(self, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Keeps the session with this router alive.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Router._op_refreshSession.invokeAsync(self, ((), context))

    def destroySession(self, context: dict[str, str] | None = None) -> None:
        """
        Destroys the session of the caller with this router.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        SessionNotExistException
            Thrown when no session exists for the caller (client).
        """
        return Router._op_destroySession.invoke(self, ((), context))

    def destroySessionAsync(self, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Destroys the session of the caller with this router.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Router._op_destroySession.invokeAsync(self, ((), context))

    def getSessionTimeout(self, context: dict[str, str] | None = None) -> int:
        """
        Gets the idle timeout used by the server-side of the connection.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        int
            The idle timeout (in seconds).
        """
        return Router._op_getSessionTimeout.invoke(self, ((), context))

    def getSessionTimeoutAsync(self, context: dict[str, str] | None = None) -> Awaitable[int]:
        """
        Gets the idle timeout used by the server-side of the connection.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[int]
            The idle timeout (in seconds).
        """
        return Router._op_getSessionTimeout.invokeAsync(self, ((), context))

    def getACMTimeout(self, context: dict[str, str] | None = None) -> int:
        """
        Gets the idle timeout used by the server-side of the connection.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        int
            The idle timeout (in seconds).
        """
        return Router._op_getACMTimeout.invoke(self, ((), context))

    def getACMTimeoutAsync(self, context: dict[str, str] | None = None) -> Awaitable[int]:
        """
        Gets the idle timeout used by the server-side of the connection.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[int]
            The idle timeout (in seconds).
        """
        return Router._op_getACMTimeout.invokeAsync(self, ((), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> RouterPrx | None:
        return checkedCast(RouterPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[RouterPrx | None ]:
        return checkedCastAsync(RouterPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> RouterPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> RouterPrx | None:
        return uncheckedCast(RouterPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::Glacier2::Router"

IcePy.defineProxy("::Glacier2::Router", RouterPrx)

class Router(_m_Ice_Router_Router, ABC):
    """
    The Glacier2 specialization of the :class:`Ice.RouterPrx` interface.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::Glacier2::Router``.
    """

    _ice_ids: Sequence[str] = ("::Glacier2::Router", "::Ice::Object", "::Ice::Router", )
    _op_getCategoryForClient: IcePy.Operation
    _op_createSession: IcePy.Operation
    _op_createSessionFromSecureConnection: IcePy.Operation
    _op_refreshSession: IcePy.Operation
    _op_destroySession: IcePy.Operation
    _op_getSessionTimeout: IcePy.Operation
    _op_getACMTimeout: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::Glacier2::Router"

    @abstractmethod
    def getCategoryForClient(self, current: Current) -> str | Awaitable[str]:
        """
        Gets a unique category that identifies the client (caller) in the router. This category must be used in the
        identities of all the client's callback objects.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        str | Awaitable[str]
            The category. It's an empty string when ``Glacier2.Server.Endpoints`` is not configured.
        """
        pass

    @abstractmethod
    def createSession(self, userId: str, password: str, current: Current) -> SessionPrx | None | Awaitable[SessionPrx | None]:
        """
        Creates a session for the client (caller) with the router. If a :class:`Glacier2.SessionManagerPrx` is configured,
        a proxy to a :class:`Glacier2.SessionPrx` object is returned to the client. Otherwise, null is returned and only an
        internal session (i.e., not visible to the client) is created.
        If a non-null session proxy is returned, it must be configured to route through the router that created it.
        This occurs automatically when the router is configured as the client's default router at the time the
        session proxy is created in the client application; otherwise, the client must configure the session proxy
        explicitly.
        
        Parameters
        ----------
        userId : str
            The user ID.
        password : str
            The password.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        SessionPrx | None | Awaitable[SessionPrx | None]
            A proxy for the newly created session, or null if no :class:`Glacier2.SessionManagerPrx` is configured.
        
        Raises
        ------
        CannotCreateSessionException
            Thrown when the session cannot be created.
        PermissionDeniedException
            Thrown when an authentication or authorization failure occurs.
        
        See Also
        --------
            :class:`Glacier2.SessionPrx`
            :class:`Glacier2.SessionManagerPrx`
            :class:`Glacier2.PermissionsVerifierPrx`
        """
        pass

    @abstractmethod
    def createSessionFromSecureConnection(self, current: Current) -> SessionPrx | None | Awaitable[SessionPrx | None]:
        """
        Creates a per-client session with the router. The user is authenticated through the SSL certificate(s)
        associated with the connection. If an :class:`Glacier2.SSLSessionManagerPrx` is configured, a proxy to a :class:`Glacier2.SessionPrx`
        object is returned to the client. Otherwise, null is returned and only an internal session (i.e., not
        visible to the client) is created.
        If a non-null session proxy is returned, it must be configured to route through the router that created it.
        This occurs automatically when the router is configured as the client's default router at the time the
        session proxy is created in the client application; otherwise, the client must configure the session proxy
        explicitly.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        SessionPrx | None | Awaitable[SessionPrx | None]
            A proxy for the newly created session, or null if no :class:`Glacier2.SSLSessionManagerPrx` is configured.
        
        Raises
        ------
        CannotCreateSessionException
            Thrown when the session cannot be created.
        PermissionDeniedException
            Thrown when an authentication or authorization failure occurs.
        
        See Also
        --------
            :class:`Glacier2.SessionPrx`
            :class:`Glacier2.SessionManagerPrx`
            :class:`Glacier2.PermissionsVerifierPrx`
        """
        pass

    @abstractmethod
    def refreshSession(self, current: Current) -> None | Awaitable[None]:
        """
        Keeps the session with this router alive.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        SessionNotExistException
            Thrown when no session exists for the caller (client).
        """
        pass

    @abstractmethod
    def destroySession(self, current: Current) -> None | Awaitable[None]:
        """
        Destroys the session of the caller with this router.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        SessionNotExistException
            Thrown when no session exists for the caller (client).
        """
        pass

    @abstractmethod
    def getSessionTimeout(self, current: Current) -> int | Awaitable[int]:
        """
        Gets the idle timeout used by the server-side of the connection.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        int | Awaitable[int]
            The idle timeout (in seconds).
        """
        pass

    @abstractmethod
    def getACMTimeout(self, current: Current) -> int | Awaitable[int]:
        """
        Gets the idle timeout used by the server-side of the connection.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        int | Awaitable[int]
            The idle timeout (in seconds).
        """
        pass

Router._op_getCategoryForClient = IcePy.Operation(
    "getCategoryForClient",
    "getCategoryForClient",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), IcePy._t_string, False, 0),
    ())

Router._op_createSession = IcePy.Operation(
    "createSession",
    "createSession",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0)),
    (),
    ((), _Glacier2_SessionPrx_t, False, 0),
    (_Glacier2_PermissionDeniedException_t, _Glacier2_CannotCreateSessionException_t))

Router._op_createSessionFromSecureConnection = IcePy.Operation(
    "createSessionFromSecureConnection",
    "createSessionFromSecureConnection",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    ((), _Glacier2_SessionPrx_t, False, 0),
    (_Glacier2_PermissionDeniedException_t, _Glacier2_CannotCreateSessionException_t))

Router._op_refreshSession = IcePy.Operation(
    "refreshSession",
    "refreshSession",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    None,
    (_Glacier2_SessionNotExistException_t,))
Router._op_refreshSession.deprecate("As of Ice 3.8, this operation does nothing.")

Router._op_destroySession = IcePy.Operation(
    "destroySession",
    "destroySession",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    None,
    (_Glacier2_SessionNotExistException_t,))

Router._op_getSessionTimeout = IcePy.Operation(
    "getSessionTimeout",
    "getSessionTimeout",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), IcePy._t_long, False, 0),
    ())

Router._op_getACMTimeout = IcePy.Operation(
    "getACMTimeout",
    "getACMTimeout",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), IcePy._t_int, False, 0),
    ())

__all__ = ["Router", "RouterPrx", "_Glacier2_RouterPrx_t"]
