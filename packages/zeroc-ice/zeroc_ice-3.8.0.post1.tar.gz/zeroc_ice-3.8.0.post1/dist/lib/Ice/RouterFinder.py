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

from Ice.RouterFinder_forward import _Ice_RouterFinderPrx_t

from Ice.Router_forward import _Ice_RouterPrx_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from Ice.Router import RouterPrx
    from collections.abc import Awaitable
    from collections.abc import Sequence


class RouterFinderPrx(ObjectPrx):
    """
    Provides access to a :class:`Ice.RouterPrx` object via a fixed identity.
    A RouterFinder is always registered with identity ``Ice/RouterFinder``. This allows clients to obtain the
    associated Router proxy with just the endpoint information of the object. For example, you can use the
    RouterFinder proxy ``Ice/RouterFinder:tcp -h somehost -p 4061`` to get the Router proxy
    ``MyGlacier2/Router:tcp -h somehost -p 4061``.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::Ice::RouterFinder``.
    """

    def getRouter(self, context: dict[str, str] | None = None) -> RouterPrx | None:
        """
        Gets a proxy to the associated :class:`Ice.RouterPrx`. The proxy might point to several replicas.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        RouterPrx | None
            The router proxy. This proxy is never null.
        """
        return RouterFinder._op_getRouter.invoke(self, ((), context))

    def getRouterAsync(self, context: dict[str, str] | None = None) -> Awaitable[RouterPrx | None]:
        """
        Gets a proxy to the associated :class:`Ice.RouterPrx`. The proxy might point to several replicas.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[RouterPrx | None]
            The router proxy. This proxy is never null.
        """
        return RouterFinder._op_getRouter.invokeAsync(self, ((), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> RouterFinderPrx | None:
        return checkedCast(RouterFinderPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[RouterFinderPrx | None ]:
        return checkedCastAsync(RouterFinderPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> RouterFinderPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> RouterFinderPrx | None:
        return uncheckedCast(RouterFinderPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::Ice::RouterFinder"

IcePy.defineProxy("::Ice::RouterFinder", RouterFinderPrx)

class RouterFinder(Object, ABC):
    """
    Provides access to a :class:`Ice.RouterPrx` object via a fixed identity.
    A RouterFinder is always registered with identity ``Ice/RouterFinder``. This allows clients to obtain the
    associated Router proxy with just the endpoint information of the object. For example, you can use the
    RouterFinder proxy ``Ice/RouterFinder:tcp -h somehost -p 4061`` to get the Router proxy
    ``MyGlacier2/Router:tcp -h somehost -p 4061``.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::Ice::RouterFinder``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::Ice::RouterFinder", )
    _op_getRouter: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::Ice::RouterFinder"

    @abstractmethod
    def getRouter(self, current: Current) -> RouterPrx | None | Awaitable[RouterPrx | None]:
        """
        Gets a proxy to the associated :class:`Ice.RouterPrx`. The proxy might point to several replicas.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        RouterPrx | None | Awaitable[RouterPrx | None]
            The router proxy. This proxy is never null.
        """
        pass

RouterFinder._op_getRouter = IcePy.Operation(
    "getRouter",
    "getRouter",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    ((), _Ice_RouterPrx_t, False, 0),
    ())

__all__ = ["RouterFinder", "RouterFinderPrx", "_Ice_RouterFinderPrx_t"]
