# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.AdapterAlreadyActiveException import _Ice_AdapterAlreadyActiveException_t

from Ice.AdapterNotFoundException import _Ice_AdapterNotFoundException_t

from Ice.InvalidReplicaGroupIdException import _Ice_InvalidReplicaGroupIdException_t

from Ice.LocatorRegistry_forward import _Ice_LocatorRegistryPrx_t

from Ice.Object import Object

from Ice.ObjectPrx import ObjectPrx
from Ice.ObjectPrx import checkedCast
from Ice.ObjectPrx import checkedCastAsync
from Ice.ObjectPrx import uncheckedCast

from Ice.ObjectPrx_forward import _Ice_ObjectPrx_t

from Ice.OperationMode import OperationMode

from Ice.Process_forward import _Ice_ProcessPrx_t

from Ice.ServerNotFoundException import _Ice_ServerNotFoundException_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from Ice.Process import ProcessPrx
    from collections.abc import Awaitable
    from collections.abc import Sequence


class LocatorRegistryPrx(ObjectPrx):
    """
    A server application registers the endpoints of its indirect object adapters with the LocatorRegistry object.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::Ice::LocatorRegistry``.
    """

    def setAdapterDirectProxy(self, id: str, proxy: ObjectPrx | None, context: dict[str, str] | None = None) -> None:
        """
        Registers or unregisters the endpoints of an object adapter.
        
        Parameters
        ----------
        id : str
            The adapter ID.
        proxy : ObjectPrx | None
            A dummy proxy created by the object adapter. ``proxy`` carries the object adapter's endpoints.
            The locator considers an object adapter to be active after it has registered its endpoints.
            When ``proxy`` is null, the endpoints are unregistered and the locator considers the object adapter inactive.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        AdapterAlreadyActiveException
            Thrown when an object adapter with the same adapter ID has already
            registered its endpoints. Since this operation is marked idempotent, this exception may be thrown when the
            Ice client runtime retries an invocation with a non-null ``proxy``.
        AdapterNotFoundException
            Thrown when the locator only allows registered object adapters to register
            their endpoints and no object adapter with this adapter ID was registered with the locator.
        """
        return LocatorRegistry._op_setAdapterDirectProxy.invoke(self, ((id, proxy), context))

    def setAdapterDirectProxyAsync(self, id: str, proxy: ObjectPrx | None, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Registers or unregisters the endpoints of an object adapter.
        
        Parameters
        ----------
        id : str
            The adapter ID.
        proxy : ObjectPrx | None
            A dummy proxy created by the object adapter. ``proxy`` carries the object adapter's endpoints.
            The locator considers an object adapter to be active after it has registered its endpoints.
            When ``proxy`` is null, the endpoints are unregistered and the locator considers the object adapter inactive.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return LocatorRegistry._op_setAdapterDirectProxy.invokeAsync(self, ((id, proxy), context))

    def setReplicatedAdapterDirectProxy(self, adapterId: str, replicaGroupId: str, proxy: ObjectPrx | None, context: dict[str, str] | None = None) -> None:
        """
        Registers or unregisters the endpoints of an object adapter. This object adapter is a member of a replica
        group.
        
        Parameters
        ----------
        adapterId : str
            The adapter ID.
        replicaGroupId : str
            The replica group ID.
        proxy : ObjectPrx | None
            A dummy proxy created by the object adapter. ``proxy`` carries the object adapter's endpoints.
            The locator considers an object adapter to be active after it has registered its endpoints. When ``proxy`` is
            null, the endpoints are unregistered and the locator considers the object adapter inactive.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        AdapterAlreadyActiveException
            Thrown when an object adapter with the same adapter ID has already
            registered its endpoints. Since this operation is marked idempotent, this exception may be thrown when the
            Ice client runtime retries an invocation with a non-null ``proxy``.
        AdapterNotFoundException
            Thrown when the locator only allows registered object adapters to register
            their endpoints and no object adapter with this adapter ID was registered with the locator.
        InvalidReplicaGroupIdException
            Thrown when the given replica group does not match the replica group
            associated with the adapter ID in the locator's database.
        """
        return LocatorRegistry._op_setReplicatedAdapterDirectProxy.invoke(self, ((adapterId, replicaGroupId, proxy), context))

    def setReplicatedAdapterDirectProxyAsync(self, adapterId: str, replicaGroupId: str, proxy: ObjectPrx | None, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Registers or unregisters the endpoints of an object adapter. This object adapter is a member of a replica
        group.
        
        Parameters
        ----------
        adapterId : str
            The adapter ID.
        replicaGroupId : str
            The replica group ID.
        proxy : ObjectPrx | None
            A dummy proxy created by the object adapter. ``proxy`` carries the object adapter's endpoints.
            The locator considers an object adapter to be active after it has registered its endpoints. When ``proxy`` is
            null, the endpoints are unregistered and the locator considers the object adapter inactive.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return LocatorRegistry._op_setReplicatedAdapterDirectProxy.invokeAsync(self, ((adapterId, replicaGroupId, proxy), context))

    def setServerProcessProxy(self, id: str, proxy: ProcessPrx | None, context: dict[str, str] | None = None) -> None:
        """
        Registers a proxy to the :class:`Ice.ProcessPrx` object of a server application.
        
        Parameters
        ----------
        id : str
            The server ID.
        proxy : ProcessPrx | None
            A proxy to the :class:`Ice.ProcessPrx` object of the server. This proxy is never null.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        ServerNotFoundException
            Thrown when the locator does not know a server application with a server ID
            of ``id``.
        """
        return LocatorRegistry._op_setServerProcessProxy.invoke(self, ((id, proxy), context))

    def setServerProcessProxyAsync(self, id: str, proxy: ProcessPrx | None, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Registers a proxy to the :class:`Ice.ProcessPrx` object of a server application.
        
        Parameters
        ----------
        id : str
            The server ID.
        proxy : ProcessPrx | None
            A proxy to the :class:`Ice.ProcessPrx` object of the server. This proxy is never null.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return LocatorRegistry._op_setServerProcessProxy.invokeAsync(self, ((id, proxy), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> LocatorRegistryPrx | None:
        return checkedCast(LocatorRegistryPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[LocatorRegistryPrx | None ]:
        return checkedCastAsync(LocatorRegistryPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> LocatorRegistryPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> LocatorRegistryPrx | None:
        return uncheckedCast(LocatorRegistryPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::Ice::LocatorRegistry"

IcePy.defineProxy("::Ice::LocatorRegistry", LocatorRegistryPrx)

class LocatorRegistry(Object, ABC):
    """
    A server application registers the endpoints of its indirect object adapters with the LocatorRegistry object.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::Ice::LocatorRegistry``.
    """

    _ice_ids: Sequence[str] = ("::Ice::LocatorRegistry", "::Ice::Object", )
    _op_setAdapterDirectProxy: IcePy.Operation
    _op_setReplicatedAdapterDirectProxy: IcePy.Operation
    _op_setServerProcessProxy: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::Ice::LocatorRegistry"

    @abstractmethod
    def setAdapterDirectProxy(self, id: str, proxy: ObjectPrx | None, current: Current) -> None | Awaitable[None]:
        """
        Registers or unregisters the endpoints of an object adapter.
        
        Parameters
        ----------
        id : str
            The adapter ID.
        proxy : ObjectPrx | None
            A dummy proxy created by the object adapter. ``proxy`` carries the object adapter's endpoints.
            The locator considers an object adapter to be active after it has registered its endpoints.
            When ``proxy`` is null, the endpoints are unregistered and the locator considers the object adapter inactive.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        AdapterAlreadyActiveException
            Thrown when an object adapter with the same adapter ID has already
            registered its endpoints. Since this operation is marked idempotent, this exception may be thrown when the
            Ice client runtime retries an invocation with a non-null ``proxy``.
        AdapterNotFoundException
            Thrown when the locator only allows registered object adapters to register
            their endpoints and no object adapter with this adapter ID was registered with the locator.
        """
        pass

    @abstractmethod
    def setReplicatedAdapterDirectProxy(self, adapterId: str, replicaGroupId: str, proxy: ObjectPrx | None, current: Current) -> None | Awaitable[None]:
        """
        Registers or unregisters the endpoints of an object adapter. This object adapter is a member of a replica
        group.
        
        Parameters
        ----------
        adapterId : str
            The adapter ID.
        replicaGroupId : str
            The replica group ID.
        proxy : ObjectPrx | None
            A dummy proxy created by the object adapter. ``proxy`` carries the object adapter's endpoints.
            The locator considers an object adapter to be active after it has registered its endpoints. When ``proxy`` is
            null, the endpoints are unregistered and the locator considers the object adapter inactive.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        AdapterAlreadyActiveException
            Thrown when an object adapter with the same adapter ID has already
            registered its endpoints. Since this operation is marked idempotent, this exception may be thrown when the
            Ice client runtime retries an invocation with a non-null ``proxy``.
        AdapterNotFoundException
            Thrown when the locator only allows registered object adapters to register
            their endpoints and no object adapter with this adapter ID was registered with the locator.
        InvalidReplicaGroupIdException
            Thrown when the given replica group does not match the replica group
            associated with the adapter ID in the locator's database.
        """
        pass

    @abstractmethod
    def setServerProcessProxy(self, id: str, proxy: ProcessPrx | None, current: Current) -> None | Awaitable[None]:
        """
        Registers a proxy to the :class:`Ice.ProcessPrx` object of a server application.
        
        Parameters
        ----------
        id : str
            The server ID.
        proxy : ProcessPrx | None
            A proxy to the :class:`Ice.ProcessPrx` object of the server. This proxy is never null.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        ServerNotFoundException
            Thrown when the locator does not know a server application with a server ID
            of ``id``.
        """
        pass

LocatorRegistry._op_setAdapterDirectProxy = IcePy.Operation(
    "setAdapterDirectProxy",
    "setAdapterDirectProxy",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), _Ice_ObjectPrx_t, False, 0)),
    (),
    None,
    (_Ice_AdapterNotFoundException_t, _Ice_AdapterAlreadyActiveException_t))

LocatorRegistry._op_setReplicatedAdapterDirectProxy = IcePy.Operation(
    "setReplicatedAdapterDirectProxy",
    "setReplicatedAdapterDirectProxy",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0), ((), _Ice_ObjectPrx_t, False, 0)),
    (),
    None,
    (_Ice_AdapterNotFoundException_t, _Ice_AdapterAlreadyActiveException_t, _Ice_InvalidReplicaGroupIdException_t))

LocatorRegistry._op_setServerProcessProxy = IcePy.Operation(
    "setServerProcessProxy",
    "setServerProcessProxy",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), _Ice_ProcessPrx_t, False, 0)),
    (),
    None,
    (_Ice_ServerNotFoundException_t,))

__all__ = ["LocatorRegistry", "LocatorRegistryPrx", "_Ice_LocatorRegistryPrx_t"]
