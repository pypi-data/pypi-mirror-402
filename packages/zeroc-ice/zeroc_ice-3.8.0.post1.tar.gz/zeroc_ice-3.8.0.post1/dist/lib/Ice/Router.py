# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.Object import Object

from Ice.ObjectProxySeq import _Ice_ObjectProxySeq_t

from Ice.ObjectPrx import ObjectPrx
from Ice.ObjectPrx import checkedCast
from Ice.ObjectPrx import checkedCastAsync
from Ice.ObjectPrx import uncheckedCast

from Ice.ObjectPrx_forward import _Ice_ObjectPrx_t

from Ice.OperationMode import OperationMode

from Ice.Router_forward import _Ice_RouterPrx_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from collections.abc import Awaitable
    from collections.abc import Sequence


class RouterPrx(ObjectPrx):
    """
    Represents an intermediary object that routes requests and replies between clients and Ice objects that are not
    directly reachable from these clients.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::Ice::Router``.
    """

    def getClientProxy(self, context: dict[str, str] | None = None) -> tuple[ObjectPrx | None, bool | None]:
        """
        Gets the router's client proxy, i.e. the proxy to use for forwarding requests from the client to the
        router. If a null proxy is returned, the client will forward requests to the router's endpoints.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        tuple[ObjectPrx | None, bool | None]
        
            A tuple containing:
                - ObjectPrx | None The router's client proxy.
                - bool | None Indicates whether or not the router supports a routing table. If ``true``, the Ice
                  runtime will call :meth:`Ice.RouterPrx.addProxiesAsync` to populate the routing table. The Ice runtime assumes the router has
                  a routing table when ``hasRoutingTable`` is not set.
        
        Notes
        -----
            Introduced in Ice 3.7.
        """
        return Router._op_getClientProxy.invoke(self, ((), context))

    def getClientProxyAsync(self, context: dict[str, str] | None = None) -> Awaitable[tuple[ObjectPrx | None, bool | None]]:
        """
        Gets the router's client proxy, i.e. the proxy to use for forwarding requests from the client to the
        router. If a null proxy is returned, the client will forward requests to the router's endpoints.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[tuple[ObjectPrx | None, bool | None]]
        
            A tuple containing:
                - ObjectPrx | None The router's client proxy.
                - bool | None Indicates whether or not the router supports a routing table. If ``true``, the Ice
                  runtime will call :meth:`Ice.RouterPrx.addProxiesAsync` to populate the routing table. The Ice runtime assumes the router has
                  a routing table when ``hasRoutingTable`` is not set.
        
        Notes
        -----
            Introduced in Ice 3.7.
        """
        return Router._op_getClientProxy.invokeAsync(self, ((), context))

    def getServerProxy(self, context: dict[str, str] | None = None) -> ObjectPrx | None:
        """
        Gets the router's server proxy, i.e. the proxy to use for forwarding requests from the server to the
        router. The Ice runtime uses the endpoints of this proxy as the published endpoints of bi-dir object
        adapters.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ObjectPrx | None
            The router's server proxy.
        """
        return Router._op_getServerProxy.invoke(self, ((), context))

    def getServerProxyAsync(self, context: dict[str, str] | None = None) -> Awaitable[ObjectPrx | None]:
        """
        Gets the router's server proxy, i.e. the proxy to use for forwarding requests from the server to the
        router. The Ice runtime uses the endpoints of this proxy as the published endpoints of bi-dir object
        adapters.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ObjectPrx | None]
            The router's server proxy.
        """
        return Router._op_getServerProxy.invokeAsync(self, ((), context))

    def addProxies(self, proxies: Sequence[ObjectPrx | None], context: dict[str, str] | None = None) -> list[ObjectPrx | None]:
        """
        Adds new proxy information to the router's routing table.
        
        Parameters
        ----------
        proxies : Sequence[ObjectPrx | None]
            The proxies to add. Adding a null proxy is an error.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        list[ObjectPrx | None]
            Proxies discarded by the router. These proxies are all non-null.
        """
        return Router._op_addProxies.invoke(self, ((proxies, ), context))

    def addProxiesAsync(self, proxies: Sequence[ObjectPrx | None], context: dict[str, str] | None = None) -> Awaitable[list[ObjectPrx | None]]:
        """
        Adds new proxy information to the router's routing table.
        
        Parameters
        ----------
        proxies : Sequence[ObjectPrx | None]
            The proxies to add. Adding a null proxy is an error.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[list[ObjectPrx | None]]
            Proxies discarded by the router. These proxies are all non-null.
        """
        return Router._op_addProxies.invokeAsync(self, ((proxies, ), context))

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
        return "::Ice::Router"

IcePy.defineProxy("::Ice::Router", RouterPrx)

class Router(Object, ABC):
    """
    Represents an intermediary object that routes requests and replies between clients and Ice objects that are not
    directly reachable from these clients.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::Ice::Router``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::Ice::Router", )
    _op_getClientProxy: IcePy.Operation
    _op_getServerProxy: IcePy.Operation
    _op_addProxies: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::Ice::Router"

    @abstractmethod
    def getClientProxy(self, current: Current) -> tuple[ObjectPrx | None, bool | None] | Awaitable[tuple[ObjectPrx | None, bool | None]]:
        """
        Gets the router's client proxy, i.e. the proxy to use for forwarding requests from the client to the
        router. If a null proxy is returned, the client will forward requests to the router's endpoints.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        tuple[ObjectPrx | None, bool | None] | Awaitable[tuple[ObjectPrx | None, bool | None]]
        
            A tuple containing:
                - ObjectPrx | None The router's client proxy.
                - bool | None Indicates whether or not the router supports a routing table. If ``true``, the Ice
                  runtime will call :meth:`Ice.RouterPrx.addProxiesAsync` to populate the routing table. The Ice runtime assumes the router has
                  a routing table when ``hasRoutingTable`` is not set.
        
        Notes
        -----
            Introduced in Ice 3.7.
        """
        pass

    @abstractmethod
    def getServerProxy(self, current: Current) -> ObjectPrx | None | Awaitable[ObjectPrx | None]:
        """
        Gets the router's server proxy, i.e. the proxy to use for forwarding requests from the server to the
        router. The Ice runtime uses the endpoints of this proxy as the published endpoints of bi-dir object
        adapters.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ObjectPrx | None | Awaitable[ObjectPrx | None]
            The router's server proxy.
        """
        pass

    @abstractmethod
    def addProxies(self, proxies: list[ObjectPrx | None], current: Current) -> Sequence[ObjectPrx | None] | Awaitable[Sequence[ObjectPrx | None]]:
        """
        Adds new proxy information to the router's routing table.
        
        Parameters
        ----------
        proxies : list[ObjectPrx | None]
            The proxies to add. Adding a null proxy is an error.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        Sequence[ObjectPrx | None] | Awaitable[Sequence[ObjectPrx | None]]
            Proxies discarded by the router. These proxies are all non-null.
        """
        pass

Router._op_getClientProxy = IcePy.Operation(
    "getClientProxy",
    "getClientProxy",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (((), IcePy._t_bool, True, 1),),
    ((), _Ice_ObjectPrx_t, False, 0),
    ())

Router._op_getServerProxy = IcePy.Operation(
    "getServerProxy",
    "getServerProxy",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), _Ice_ObjectPrx_t, False, 0),
    ())

Router._op_addProxies = IcePy.Operation(
    "addProxies",
    "addProxies",
    OperationMode.Idempotent,
    None,
    (),
    (((), _Ice_ObjectProxySeq_t, False, 0),),
    (),
    ((), _Ice_ObjectProxySeq_t, False, 0),
    ())

__all__ = ["Router", "RouterPrx", "_Ice_RouterPrx_t"]
