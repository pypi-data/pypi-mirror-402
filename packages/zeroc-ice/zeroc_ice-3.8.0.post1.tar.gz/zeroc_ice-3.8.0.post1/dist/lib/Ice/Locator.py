# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.AdapterNotFoundException import _Ice_AdapterNotFoundException_t

from Ice.Identity import _Ice_Identity_t

from Ice.LocatorRegistry_forward import _Ice_LocatorRegistryPrx_t

from Ice.Locator_forward import _Ice_LocatorPrx_t

from Ice.Object import Object

from Ice.ObjectNotFoundException import _Ice_ObjectNotFoundException_t

from Ice.ObjectPrx import ObjectPrx
from Ice.ObjectPrx import checkedCast
from Ice.ObjectPrx import checkedCastAsync
from Ice.ObjectPrx import uncheckedCast

from Ice.ObjectPrx_forward import _Ice_ObjectPrx_t

from Ice.OperationMode import OperationMode

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from Ice.Identity import Identity
    from Ice.LocatorRegistry import LocatorRegistryPrx
    from collections.abc import Awaitable
    from collections.abc import Sequence


class LocatorPrx(ObjectPrx):
    """
    Client applications use the Locator object to resolve Ice indirect proxies. This object also allows
    server applications to retrieve a proxy to the associated :class:`Ice.LocatorRegistryPrx` object where they can register
    their object adapters.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::Ice::Locator``.
    """

    def findObjectById(self, id: Identity, context: dict[str, str] | None = None) -> ObjectPrx | None:
        """
        Finds an object by identity and returns a dummy proxy with the endpoint(s) that can be used to reach this
        object. This dummy proxy may be an indirect proxy that requires further resolution using
        :meth:`Ice.LocatorPrx.findAdapterByIdAsync`.
        
        Parameters
        ----------
        id : Identity
            The identity.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ObjectPrx | None
            A dummy proxy, or null if an object with the requested identity was not found.
        
        Raises
        ------
        ObjectNotFoundException
            Thrown when an object with the requested identity was not found. The caller
            should treat this exception like a null return value.
        """
        return Locator._op_findObjectById.invoke(self, ((id, ), context))

    def findObjectByIdAsync(self, id: Identity, context: dict[str, str] | None = None) -> Awaitable[ObjectPrx | None]:
        """
        Finds an object by identity and returns a dummy proxy with the endpoint(s) that can be used to reach this
        object. This dummy proxy may be an indirect proxy that requires further resolution using
        :meth:`Ice.LocatorPrx.findAdapterByIdAsync`.
        
        Parameters
        ----------
        id : Identity
            The identity.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ObjectPrx | None]
            A dummy proxy, or null if an object with the requested identity was not found.
        """
        return Locator._op_findObjectById.invokeAsync(self, ((id, ), context))

    def findAdapterById(self, id: str, context: dict[str, str] | None = None) -> ObjectPrx | None:
        """
        Finds an object adapter by adapter ID and returns a dummy proxy with the object adapter's endpoint(s).
        
        Parameters
        ----------
        id : str
            The adapter ID.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ObjectPrx | None
            A dummy proxy with the adapter's endpoints, or null if an object adapter with ``id`` was not found.
        
        Raises
        ------
        AdapterNotFoundException
            Thrown when an object adapter with this adapter ID was not found. The
            caller should treat this exception like a null return value.
        """
        return Locator._op_findAdapterById.invoke(self, ((id, ), context))

    def findAdapterByIdAsync(self, id: str, context: dict[str, str] | None = None) -> Awaitable[ObjectPrx | None]:
        """
        Finds an object adapter by adapter ID and returns a dummy proxy with the object adapter's endpoint(s).
        
        Parameters
        ----------
        id : str
            The adapter ID.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ObjectPrx | None]
            A dummy proxy with the adapter's endpoints, or null if an object adapter with ``id`` was not found.
        """
        return Locator._op_findAdapterById.invokeAsync(self, ((id, ), context))

    def getRegistry(self, context: dict[str, str] | None = None) -> LocatorRegistryPrx | None:
        """
        Gets a proxy to the locator registry.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        LocatorRegistryPrx | None
            A proxy to the locator registry, or null if this locator has no associated registry.
        """
        return Locator._op_getRegistry.invoke(self, ((), context))

    def getRegistryAsync(self, context: dict[str, str] | None = None) -> Awaitable[LocatorRegistryPrx | None]:
        """
        Gets a proxy to the locator registry.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[LocatorRegistryPrx | None]
            A proxy to the locator registry, or null if this locator has no associated registry.
        """
        return Locator._op_getRegistry.invokeAsync(self, ((), context))

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
        return "::Ice::Locator"

IcePy.defineProxy("::Ice::Locator", LocatorPrx)

class Locator(Object, ABC):
    """
    Client applications use the Locator object to resolve Ice indirect proxies. This object also allows
    server applications to retrieve a proxy to the associated :class:`Ice.LocatorRegistryPrx` object where they can register
    their object adapters.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::Ice::Locator``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Locator", "::Ice::Object", )
    _op_findObjectById: IcePy.Operation
    _op_findAdapterById: IcePy.Operation
    _op_getRegistry: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::Ice::Locator"

    @abstractmethod
    def findObjectById(self, id: Identity, current: Current) -> ObjectPrx | None | Awaitable[ObjectPrx | None]:
        """
        Finds an object by identity and returns a dummy proxy with the endpoint(s) that can be used to reach this
        object. This dummy proxy may be an indirect proxy that requires further resolution using
        :meth:`Ice.LocatorPrx.findAdapterByIdAsync`.
        
        Parameters
        ----------
        id : Identity
            The identity.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ObjectPrx | None | Awaitable[ObjectPrx | None]
            A dummy proxy, or null if an object with the requested identity was not found.
        
        Raises
        ------
        ObjectNotFoundException
            Thrown when an object with the requested identity was not found. The caller
            should treat this exception like a null return value.
        """
        pass

    @abstractmethod
    def findAdapterById(self, id: str, current: Current) -> ObjectPrx | None | Awaitable[ObjectPrx | None]:
        """
        Finds an object adapter by adapter ID and returns a dummy proxy with the object adapter's endpoint(s).
        
        Parameters
        ----------
        id : str
            The adapter ID.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ObjectPrx | None | Awaitable[ObjectPrx | None]
            A dummy proxy with the adapter's endpoints, or null if an object adapter with ``id`` was not found.
        
        Raises
        ------
        AdapterNotFoundException
            Thrown when an object adapter with this adapter ID was not found. The
            caller should treat this exception like a null return value.
        """
        pass

    @abstractmethod
    def getRegistry(self, current: Current) -> LocatorRegistryPrx | None | Awaitable[LocatorRegistryPrx | None]:
        """
        Gets a proxy to the locator registry.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        LocatorRegistryPrx | None | Awaitable[LocatorRegistryPrx | None]
            A proxy to the locator registry, or null if this locator has no associated registry.
        """
        pass

Locator._op_findObjectById = IcePy.Operation(
    "findObjectById",
    "findObjectById",
    OperationMode.Idempotent,
    None,
    (),
    (((), _Ice_Identity_t, False, 0),),
    (),
    ((), _Ice_ObjectPrx_t, False, 0),
    (_Ice_ObjectNotFoundException_t,))

Locator._op_findAdapterById = IcePy.Operation(
    "findAdapterById",
    "findAdapterById",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _Ice_ObjectPrx_t, False, 0),
    (_Ice_AdapterNotFoundException_t,))

Locator._op_getRegistry = IcePy.Operation(
    "getRegistry",
    "getRegistry",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), _Ice_LocatorRegistryPrx_t, False, 0),
    ())

__all__ = ["Locator", "LocatorPrx", "_Ice_LocatorPrx_t"]
