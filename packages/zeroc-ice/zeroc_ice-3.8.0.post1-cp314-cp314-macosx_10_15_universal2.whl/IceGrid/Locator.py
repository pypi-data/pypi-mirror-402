# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.AdapterNotFoundException import _Ice_AdapterNotFoundException_t

from Ice.Identity import _Ice_Identity_t

from Ice.Locator import Locator as _m_Ice_Locator_Locator
from Ice.Locator import LocatorPrx as _m_Ice_Locator_LocatorPrx

from Ice.LocatorRegistry_forward import _Ice_LocatorRegistryPrx_t

from Ice.ObjectNotFoundException import _Ice_ObjectNotFoundException_t

from Ice.ObjectPrx import checkedCast
from Ice.ObjectPrx import checkedCastAsync
from Ice.ObjectPrx import uncheckedCast

from Ice.ObjectPrx_forward import _Ice_ObjectPrx_t

from Ice.OperationMode import OperationMode

from IceGrid.Locator_forward import _IceGrid_LocatorPrx_t

from IceGrid.Query_forward import _IceGrid_QueryPrx_t

from IceGrid.Registry_forward import _IceGrid_RegistryPrx_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from Ice.Identity import Identity
    from Ice.LocatorRegistry import LocatorRegistryPrx
    from Ice.ObjectPrx import ObjectPrx
    from IceGrid.Query import QueryPrx
    from IceGrid.Registry import RegistryPrx
    from collections.abc import Awaitable
    from collections.abc import Sequence


class LocatorPrx(_m_Ice_Locator_LocatorPrx):
    """
    Provides access to the :class:`IceGrid.QueryPrx` and :class:`IceGrid.RegistryPrx` objects implemented by the IceGrid registry.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::IceGrid::Locator``.
    """

    def getLocalRegistry(self, context: dict[str, str] | None = None) -> RegistryPrx | None:
        """
        Gets a proxy to the registry object hosted by this IceGrid registry.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        RegistryPrx | None
            A proxy to the registry object. This proxy is never null.
        """
        return Locator._op_getLocalRegistry.invoke(self, ((), context))

    def getLocalRegistryAsync(self, context: dict[str, str] | None = None) -> Awaitable[RegistryPrx | None]:
        """
        Gets a proxy to the registry object hosted by this IceGrid registry.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[RegistryPrx | None]
            A proxy to the registry object. This proxy is never null.
        """
        return Locator._op_getLocalRegistry.invokeAsync(self, ((), context))

    def getLocalQuery(self, context: dict[str, str] | None = None) -> QueryPrx | None:
        """
        Gets a proxy to the query object hosted by this IceGrid registry.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        QueryPrx | None
            A proxy to the query object. This proxy is never null.
        """
        return Locator._op_getLocalQuery.invoke(self, ((), context))

    def getLocalQueryAsync(self, context: dict[str, str] | None = None) -> Awaitable[QueryPrx | None]:
        """
        Gets a proxy to the query object hosted by this IceGrid registry.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[QueryPrx | None]
            A proxy to the query object. This proxy is never null.
        """
        return Locator._op_getLocalQuery.invokeAsync(self, ((), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> LocatorPrx | None:
        return checkedCast(LocatorPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[LocatorPrx | None ]:
        return checkedCastAsync(LocatorPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> LocatorPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> LocatorPrx | None:
        return uncheckedCast(LocatorPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::Locator"

IcePy.defineProxy("::IceGrid::Locator", LocatorPrx)

class Locator(_m_Ice_Locator_Locator, ABC):
    """
    Provides access to the :class:`IceGrid.QueryPrx` and :class:`IceGrid.RegistryPrx` objects implemented by the IceGrid registry.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::IceGrid::Locator``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Locator", "::Ice::Object", "::IceGrid::Locator", )
    _op_getLocalRegistry: IcePy.Operation
    _op_getLocalQuery: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::Locator"

    @abstractmethod
    def getLocalRegistry(self, current: Current) -> RegistryPrx | None | Awaitable[RegistryPrx | None]:
        """
        Gets a proxy to the registry object hosted by this IceGrid registry.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        RegistryPrx | None | Awaitable[RegistryPrx | None]
            A proxy to the registry object. This proxy is never null.
        """
        pass

    @abstractmethod
    def getLocalQuery(self, current: Current) -> QueryPrx | None | Awaitable[QueryPrx | None]:
        """
        Gets a proxy to the query object hosted by this IceGrid registry.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        QueryPrx | None | Awaitable[QueryPrx | None]
            A proxy to the query object. This proxy is never null.
        """
        pass

Locator._op_getLocalRegistry = IcePy.Operation(
    "getLocalRegistry",
    "getLocalRegistry",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), _IceGrid_RegistryPrx_t, False, 0),
    ())

Locator._op_getLocalQuery = IcePy.Operation(
    "getLocalQuery",
    "getLocalQuery",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), _IceGrid_QueryPrx_t, False, 0),
    ())

__all__ = ["Locator", "LocatorPrx", "_IceGrid_LocatorPrx_t"]
