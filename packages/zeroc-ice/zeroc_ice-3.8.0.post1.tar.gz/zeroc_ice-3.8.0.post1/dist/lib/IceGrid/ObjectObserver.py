# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.Identity import _Ice_Identity_t

from Ice.Object import Object

from Ice.ObjectPrx import ObjectPrx
from Ice.ObjectPrx import checkedCast
from Ice.ObjectPrx import checkedCastAsync
from Ice.ObjectPrx import uncheckedCast

from Ice.OperationMode import OperationMode

from IceGrid.ObjectInfo import _IceGrid_ObjectInfo_t

from IceGrid.ObjectInfoSeq import _IceGrid_ObjectInfoSeq_t

from IceGrid.ObjectObserver_forward import _IceGrid_ObjectObserverPrx_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from Ice.Identity import Identity
    from IceGrid.ObjectInfo import ObjectInfo
    from collections.abc import Awaitable
    from collections.abc import Sequence


class ObjectObserverPrx(ObjectPrx):
    """
    Monitors well-known objects that are added, updated or removed using :class:`IceGrid.AdminPrx`.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::IceGrid::ObjectObserver``.
    """

    def objectInit(self, objects: Sequence[ObjectInfo], context: dict[str, str] | None = None) -> None:
        """
        Provides the initial list of well-known objects to the observer.
        
        Parameters
        ----------
        objects : Sequence[ObjectInfo]
            The well-known objects registered using :class:`IceGrid.AdminPrx`.
        context : dict[str, str]
            The request context for the invocation.
        """
        return ObjectObserver._op_objectInit.invoke(self, ((objects, ), context))

    def objectInitAsync(self, objects: Sequence[ObjectInfo], context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Provides the initial list of well-known objects to the observer.
        
        Parameters
        ----------
        objects : Sequence[ObjectInfo]
            The well-known objects registered using :class:`IceGrid.AdminPrx`.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return ObjectObserver._op_objectInit.invokeAsync(self, ((objects, ), context))

    def objectAdded(self, info: ObjectInfo, context: dict[str, str] | None = None) -> None:
        """
        Notifies the observer that a well-known object was added.
        
        Parameters
        ----------
        info : ObjectInfo
            The details of the new object.
        context : dict[str, str]
            The request context for the invocation.
        """
        return ObjectObserver._op_objectAdded.invoke(self, ((info, ), context))

    def objectAddedAsync(self, info: ObjectInfo, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Notifies the observer that a well-known object was added.
        
        Parameters
        ----------
        info : ObjectInfo
            The details of the new object.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return ObjectObserver._op_objectAdded.invokeAsync(self, ((info, ), context))

    def objectUpdated(self, info: ObjectInfo, context: dict[str, str] | None = None) -> None:
        """
        Notifies the observer that a well-known object was updated.
        
        Parameters
        ----------
        info : ObjectInfo
            The details of the updated object.
        context : dict[str, str]
            The request context for the invocation.
        """
        return ObjectObserver._op_objectUpdated.invoke(self, ((info, ), context))

    def objectUpdatedAsync(self, info: ObjectInfo, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Notifies the observer that a well-known object was updated.
        
        Parameters
        ----------
        info : ObjectInfo
            The details of the updated object.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return ObjectObserver._op_objectUpdated.invokeAsync(self, ((info, ), context))

    def objectRemoved(self, id: Identity, context: dict[str, str] | None = None) -> None:
        """
        Notifies the observer that a well-known object was removed.
        
        Parameters
        ----------
        id : Identity
            The identity of the removed object.
        context : dict[str, str]
            The request context for the invocation.
        """
        return ObjectObserver._op_objectRemoved.invoke(self, ((id, ), context))

    def objectRemovedAsync(self, id: Identity, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Notifies the observer that a well-known object was removed.
        
        Parameters
        ----------
        id : Identity
            The identity of the removed object.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return ObjectObserver._op_objectRemoved.invokeAsync(self, ((id, ), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> ObjectObserverPrx | None:
        return checkedCast(ObjectObserverPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[ObjectObserverPrx | None ]:
        return checkedCastAsync(ObjectObserverPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> ObjectObserverPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> ObjectObserverPrx | None:
        return uncheckedCast(ObjectObserverPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::ObjectObserver"

IcePy.defineProxy("::IceGrid::ObjectObserver", ObjectObserverPrx)

class ObjectObserver(Object, ABC):
    """
    Monitors well-known objects that are added, updated or removed using :class:`IceGrid.AdminPrx`.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::IceGrid::ObjectObserver``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::IceGrid::ObjectObserver", )
    _op_objectInit: IcePy.Operation
    _op_objectAdded: IcePy.Operation
    _op_objectUpdated: IcePy.Operation
    _op_objectRemoved: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::ObjectObserver"

    @abstractmethod
    def objectInit(self, objects: list[ObjectInfo], current: Current) -> None | Awaitable[None]:
        """
        Provides the initial list of well-known objects to the observer.
        
        Parameters
        ----------
        objects : list[ObjectInfo]
            The well-known objects registered using :class:`IceGrid.AdminPrx`.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def objectAdded(self, info: ObjectInfo, current: Current) -> None | Awaitable[None]:
        """
        Notifies the observer that a well-known object was added.
        
        Parameters
        ----------
        info : ObjectInfo
            The details of the new object.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def objectUpdated(self, info: ObjectInfo, current: Current) -> None | Awaitable[None]:
        """
        Notifies the observer that a well-known object was updated.
        
        Parameters
        ----------
        info : ObjectInfo
            The details of the updated object.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def objectRemoved(self, id: Identity, current: Current) -> None | Awaitable[None]:
        """
        Notifies the observer that a well-known object was removed.
        
        Parameters
        ----------
        id : Identity
            The identity of the removed object.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

ObjectObserver._op_objectInit = IcePy.Operation(
    "objectInit",
    "objectInit",
    OperationMode.Normal,
    None,
    (),
    (((), _IceGrid_ObjectInfoSeq_t, False, 0),),
    (),
    None,
    ())

ObjectObserver._op_objectAdded = IcePy.Operation(
    "objectAdded",
    "objectAdded",
    OperationMode.Normal,
    None,
    (),
    (((), _IceGrid_ObjectInfo_t, False, 0),),
    (),
    None,
    ())

ObjectObserver._op_objectUpdated = IcePy.Operation(
    "objectUpdated",
    "objectUpdated",
    OperationMode.Normal,
    None,
    (),
    (((), _IceGrid_ObjectInfo_t, False, 0),),
    (),
    None,
    ())

ObjectObserver._op_objectRemoved = IcePy.Operation(
    "objectRemoved",
    "objectRemoved",
    OperationMode.Normal,
    None,
    (),
    (((), _Ice_Identity_t, False, 0),),
    (),
    None,
    ())

__all__ = ["ObjectObserver", "ObjectObserverPrx", "_IceGrid_ObjectObserverPrx_t"]
