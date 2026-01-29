# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.Identity import _Ice_Identity_t

from Ice.Object import Object

from Ice.ObjectProxySeq import _Ice_ObjectProxySeq_t

from Ice.ObjectPrx import ObjectPrx
from Ice.ObjectPrx import checkedCast
from Ice.ObjectPrx import checkedCastAsync
from Ice.ObjectPrx import uncheckedCast

from Ice.ObjectPrx_forward import _Ice_ObjectPrx_t

from Ice.OperationMode import OperationMode

from IceGrid.LoadSample import _IceGrid_LoadSample_t

from IceGrid.Query_forward import _IceGrid_QueryPrx_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from Ice.Identity import Identity
    from IceGrid.LoadSample import LoadSample
    from collections.abc import Awaitable
    from collections.abc import Sequence


class QueryPrx(ObjectPrx):
    """
    Finds well-known Ice objects registered with the IceGrid registry.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::IceGrid::Query``.
    """

    def findObjectById(self, id: Identity, context: dict[str, str] | None = None) -> ObjectPrx | None:
        """
        Finds a well-known object by identity.
        
        Parameters
        ----------
        id : Identity
            The identity.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ObjectPrx | None
            A proxy to the well-known object, or null if no such object is registered.
        """
        return Query._op_findObjectById.invoke(self, ((id, ), context))

    def findObjectByIdAsync(self, id: Identity, context: dict[str, str] | None = None) -> Awaitable[ObjectPrx | None]:
        """
        Finds a well-known object by identity.
        
        Parameters
        ----------
        id : Identity
            The identity.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ObjectPrx | None]
            A proxy to the well-known object, or null if no such object is registered.
        """
        return Query._op_findObjectById.invokeAsync(self, ((id, ), context))

    def findObjectByType(self, type: str, context: dict[str, str] | None = None) -> ObjectPrx | None:
        """
        Finds a well-known object by type. If there are several objects registered for the given type, the object is
        randomly selected.
        
        Parameters
        ----------
        type : str
            The object type.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ObjectPrx | None
            A proxy to a well-known object with the specified type, or null if no such object is registered.
        """
        return Query._op_findObjectByType.invoke(self, ((type, ), context))

    def findObjectByTypeAsync(self, type: str, context: dict[str, str] | None = None) -> Awaitable[ObjectPrx | None]:
        """
        Finds a well-known object by type. If there are several objects registered for the given type, the object is
        randomly selected.
        
        Parameters
        ----------
        type : str
            The object type.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ObjectPrx | None]
            A proxy to a well-known object with the specified type, or null if no such object is registered.
        """
        return Query._op_findObjectByType.invokeAsync(self, ((type, ), context))

    def findObjectByTypeOnLeastLoadedNode(self, type: str, sample: LoadSample, context: dict[str, str] | None = None) -> ObjectPrx | None:
        """
        Finds a well-known object by type on the least-loaded node. If the registry does not know which node hosts
        the object (for example, because the object was registered with a direct proxy), the registry assumes the
        object is hosted on a node that has a load average of 1.0.
        
        Parameters
        ----------
        type : str
            The object type.
        sample : LoadSample
            The sampling interval.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ObjectPrx | None
            A proxy to the well-known object, or null if no such object is registered.
        """
        return Query._op_findObjectByTypeOnLeastLoadedNode.invoke(self, ((type, sample), context))

    def findObjectByTypeOnLeastLoadedNodeAsync(self, type: str, sample: LoadSample, context: dict[str, str] | None = None) -> Awaitable[ObjectPrx | None]:
        """
        Finds a well-known object by type on the least-loaded node. If the registry does not know which node hosts
        the object (for example, because the object was registered with a direct proxy), the registry assumes the
        object is hosted on a node that has a load average of 1.0.
        
        Parameters
        ----------
        type : str
            The object type.
        sample : LoadSample
            The sampling interval.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ObjectPrx | None]
            A proxy to the well-known object, or null if no such object is registered.
        """
        return Query._op_findObjectByTypeOnLeastLoadedNode.invokeAsync(self, ((type, sample), context))

    def findAllObjectsByType(self, type: str, context: dict[str, str] | None = None) -> list[ObjectPrx | None]:
        """
        Finds all the well-known objects with the given type.
        
        Parameters
        ----------
        type : str
            The object type.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        list[ObjectPrx | None]
            A list of proxies to the well-known objects with the specified type. Can be empty.
        """
        return Query._op_findAllObjectsByType.invoke(self, ((type, ), context))

    def findAllObjectsByTypeAsync(self, type: str, context: dict[str, str] | None = None) -> Awaitable[list[ObjectPrx | None]]:
        """
        Finds all the well-known objects with the given type.
        
        Parameters
        ----------
        type : str
            The object type.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[list[ObjectPrx | None]]
            A list of proxies to the well-known objects with the specified type. Can be empty.
        """
        return Query._op_findAllObjectsByType.invokeAsync(self, ((type, ), context))

    def findAllReplicas(self, proxy: ObjectPrx | None, context: dict[str, str] | None = None) -> list[ObjectPrx | None]:
        """
        Finds all the replicas of a well-known object.
        
        Parameters
        ----------
        proxy : ObjectPrx | None
            A proxy that identifies the well-known object.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        list[ObjectPrx | None]
            A list of proxies to the replicas of the well-known object specified by ``proxy``. Can be empty.
        """
        return Query._op_findAllReplicas.invoke(self, ((proxy, ), context))

    def findAllReplicasAsync(self, proxy: ObjectPrx | None, context: dict[str, str] | None = None) -> Awaitable[list[ObjectPrx | None]]:
        """
        Finds all the replicas of a well-known object.
        
        Parameters
        ----------
        proxy : ObjectPrx | None
            A proxy that identifies the well-known object.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[list[ObjectPrx | None]]
            A list of proxies to the replicas of the well-known object specified by ``proxy``. Can be empty.
        """
        return Query._op_findAllReplicas.invokeAsync(self, ((proxy, ), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> QueryPrx | None:
        return checkedCast(QueryPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[QueryPrx | None ]:
        return checkedCastAsync(QueryPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> QueryPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> QueryPrx | None:
        return uncheckedCast(QueryPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::Query"

IcePy.defineProxy("::IceGrid::Query", QueryPrx)

class Query(Object, ABC):
    """
    Finds well-known Ice objects registered with the IceGrid registry.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::IceGrid::Query``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::IceGrid::Query", )
    _op_findObjectById: IcePy.Operation
    _op_findObjectByType: IcePy.Operation
    _op_findObjectByTypeOnLeastLoadedNode: IcePy.Operation
    _op_findAllObjectsByType: IcePy.Operation
    _op_findAllReplicas: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::Query"

    @abstractmethod
    def findObjectById(self, id: Identity, current: Current) -> ObjectPrx | None | Awaitable[ObjectPrx | None]:
        """
        Finds a well-known object by identity.
        
        Parameters
        ----------
        id : Identity
            The identity.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ObjectPrx | None | Awaitable[ObjectPrx | None]
            A proxy to the well-known object, or null if no such object is registered.
        """
        pass

    @abstractmethod
    def findObjectByType(self, type: str, current: Current) -> ObjectPrx | None | Awaitable[ObjectPrx | None]:
        """
        Finds a well-known object by type. If there are several objects registered for the given type, the object is
        randomly selected.
        
        Parameters
        ----------
        type : str
            The object type.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ObjectPrx | None | Awaitable[ObjectPrx | None]
            A proxy to a well-known object with the specified type, or null if no such object is registered.
        """
        pass

    @abstractmethod
    def findObjectByTypeOnLeastLoadedNode(self, type: str, sample: LoadSample, current: Current) -> ObjectPrx | None | Awaitable[ObjectPrx | None]:
        """
        Finds a well-known object by type on the least-loaded node. If the registry does not know which node hosts
        the object (for example, because the object was registered with a direct proxy), the registry assumes the
        object is hosted on a node that has a load average of 1.0.
        
        Parameters
        ----------
        type : str
            The object type.
        sample : LoadSample
            The sampling interval.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ObjectPrx | None | Awaitable[ObjectPrx | None]
            A proxy to the well-known object, or null if no such object is registered.
        """
        pass

    @abstractmethod
    def findAllObjectsByType(self, type: str, current: Current) -> Sequence[ObjectPrx | None] | Awaitable[Sequence[ObjectPrx | None]]:
        """
        Finds all the well-known objects with the given type.
        
        Parameters
        ----------
        type : str
            The object type.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        Sequence[ObjectPrx | None] | Awaitable[Sequence[ObjectPrx | None]]
            A list of proxies to the well-known objects with the specified type. Can be empty.
        """
        pass

    @abstractmethod
    def findAllReplicas(self, proxy: ObjectPrx | None, current: Current) -> Sequence[ObjectPrx | None] | Awaitable[Sequence[ObjectPrx | None]]:
        """
        Finds all the replicas of a well-known object.
        
        Parameters
        ----------
        proxy : ObjectPrx | None
            A proxy that identifies the well-known object.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        Sequence[ObjectPrx | None] | Awaitable[Sequence[ObjectPrx | None]]
            A list of proxies to the replicas of the well-known object specified by ``proxy``. Can be empty.
        """
        pass

Query._op_findObjectById = IcePy.Operation(
    "findObjectById",
    "findObjectById",
    OperationMode.Idempotent,
    None,
    (),
    (((), _Ice_Identity_t, False, 0),),
    (),
    ((), _Ice_ObjectPrx_t, False, 0),
    ())

Query._op_findObjectByType = IcePy.Operation(
    "findObjectByType",
    "findObjectByType",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _Ice_ObjectPrx_t, False, 0),
    ())

Query._op_findObjectByTypeOnLeastLoadedNode = IcePy.Operation(
    "findObjectByTypeOnLeastLoadedNode",
    "findObjectByTypeOnLeastLoadedNode",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), _IceGrid_LoadSample_t, False, 0)),
    (),
    ((), _Ice_ObjectPrx_t, False, 0),
    ())

Query._op_findAllObjectsByType = IcePy.Operation(
    "findAllObjectsByType",
    "findAllObjectsByType",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _Ice_ObjectProxySeq_t, False, 0),
    ())

Query._op_findAllReplicas = IcePy.Operation(
    "findAllReplicas",
    "findAllReplicas",
    OperationMode.Idempotent,
    None,
    (),
    (((), _Ice_ObjectPrx_t, False, 0),),
    (),
    ((), _Ice_ObjectProxySeq_t, False, 0),
    ())

__all__ = ["Query", "QueryPrx", "_IceGrid_QueryPrx_t"]
