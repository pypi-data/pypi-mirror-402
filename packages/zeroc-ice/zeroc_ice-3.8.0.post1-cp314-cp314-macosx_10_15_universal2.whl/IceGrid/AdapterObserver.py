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

from IceGrid.AdapterInfo import _IceGrid_AdapterInfo_t

from IceGrid.AdapterInfoSeq import _IceGrid_AdapterInfoSeq_t

from IceGrid.AdapterObserver_forward import _IceGrid_AdapterObserverPrx_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from IceGrid.AdapterInfo import AdapterInfo
    from collections.abc import Awaitable
    from collections.abc import Sequence


class AdapterObserverPrx(ObjectPrx):
    """
    Monitors dynamically-registered object adapters.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::IceGrid::AdapterObserver``.
    """

    def adapterInit(self, adpts: Sequence[AdapterInfo], context: dict[str, str] | None = None) -> None:
        """
        Provides the initial list of dynamically registered adapters to the observer.
        
        Parameters
        ----------
        adpts : Sequence[AdapterInfo]
            The adapters that were dynamically registered with the registry.
        context : dict[str, str]
            The request context for the invocation.
        """
        return AdapterObserver._op_adapterInit.invoke(self, ((adpts, ), context))

    def adapterInitAsync(self, adpts: Sequence[AdapterInfo], context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Provides the initial list of dynamically registered adapters to the observer.
        
        Parameters
        ----------
        adpts : Sequence[AdapterInfo]
            The adapters that were dynamically registered with the registry.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return AdapterObserver._op_adapterInit.invokeAsync(self, ((adpts, ), context))

    def adapterAdded(self, info: AdapterInfo, context: dict[str, str] | None = None) -> None:
        """
        Notifies the observer that a dynamically-registered adapter was added.
        
        Parameters
        ----------
        info : AdapterInfo
            The details of the new adapter.
        context : dict[str, str]
            The request context for the invocation.
        """
        return AdapterObserver._op_adapterAdded.invoke(self, ((info, ), context))

    def adapterAddedAsync(self, info: AdapterInfo, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Notifies the observer that a dynamically-registered adapter was added.
        
        Parameters
        ----------
        info : AdapterInfo
            The details of the new adapter.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return AdapterObserver._op_adapterAdded.invokeAsync(self, ((info, ), context))

    def adapterUpdated(self, info: AdapterInfo, context: dict[str, str] | None = None) -> None:
        """
        Parameters
        ----------
        info : AdapterInfo
            The details of the updated adapter.
        context : dict[str, str]
            The request context for the invocation.
        """
        return AdapterObserver._op_adapterUpdated.invoke(self, ((info, ), context))

    def adapterUpdatedAsync(self, info: AdapterInfo, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Parameters
        ----------
        info : AdapterInfo
            The details of the updated adapter.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return AdapterObserver._op_adapterUpdated.invokeAsync(self, ((info, ), context))

    def adapterRemoved(self, id: str, context: dict[str, str] | None = None) -> None:
        """
        Notifies the observer that a dynamically-registered adapter was removed.
        
        Parameters
        ----------
        id : str
            The ID of the removed adapter.
        context : dict[str, str]
            The request context for the invocation.
        """
        return AdapterObserver._op_adapterRemoved.invoke(self, ((id, ), context))

    def adapterRemovedAsync(self, id: str, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Notifies the observer that a dynamically-registered adapter was removed.
        
        Parameters
        ----------
        id : str
            The ID of the removed adapter.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return AdapterObserver._op_adapterRemoved.invokeAsync(self, ((id, ), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> AdapterObserverPrx | None:
        return checkedCast(AdapterObserverPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[AdapterObserverPrx | None ]:
        return checkedCastAsync(AdapterObserverPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> AdapterObserverPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> AdapterObserverPrx | None:
        return uncheckedCast(AdapterObserverPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::AdapterObserver"

IcePy.defineProxy("::IceGrid::AdapterObserver", AdapterObserverPrx)

class AdapterObserver(Object, ABC):
    """
    Monitors dynamically-registered object adapters.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::IceGrid::AdapterObserver``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::IceGrid::AdapterObserver", )
    _op_adapterInit: IcePy.Operation
    _op_adapterAdded: IcePy.Operation
    _op_adapterUpdated: IcePy.Operation
    _op_adapterRemoved: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::AdapterObserver"

    @abstractmethod
    def adapterInit(self, adpts: list[AdapterInfo], current: Current) -> None | Awaitable[None]:
        """
        Provides the initial list of dynamically registered adapters to the observer.
        
        Parameters
        ----------
        adpts : list[AdapterInfo]
            The adapters that were dynamically registered with the registry.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def adapterAdded(self, info: AdapterInfo, current: Current) -> None | Awaitable[None]:
        """
        Notifies the observer that a dynamically-registered adapter was added.
        
        Parameters
        ----------
        info : AdapterInfo
            The details of the new adapter.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def adapterUpdated(self, info: AdapterInfo, current: Current) -> None | Awaitable[None]:
        """
        Parameters
        ----------
        info : AdapterInfo
            The details of the updated adapter.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def adapterRemoved(self, id: str, current: Current) -> None | Awaitable[None]:
        """
        Notifies the observer that a dynamically-registered adapter was removed.
        
        Parameters
        ----------
        id : str
            The ID of the removed adapter.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

AdapterObserver._op_adapterInit = IcePy.Operation(
    "adapterInit",
    "adapterInit",
    OperationMode.Normal,
    None,
    (),
    (((), _IceGrid_AdapterInfoSeq_t, False, 0),),
    (),
    None,
    ())

AdapterObserver._op_adapterAdded = IcePy.Operation(
    "adapterAdded",
    "adapterAdded",
    OperationMode.Normal,
    None,
    (),
    (((), _IceGrid_AdapterInfo_t, False, 0),),
    (),
    None,
    ())

AdapterObserver._op_adapterUpdated = IcePy.Operation(
    "adapterUpdated",
    "adapterUpdated",
    OperationMode.Normal,
    None,
    (),
    (((), _IceGrid_AdapterInfo_t, False, 0),),
    (),
    None,
    ())

AdapterObserver._op_adapterRemoved = IcePy.Operation(
    "adapterRemoved",
    "adapterRemoved",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    None,
    ())

__all__ = ["AdapterObserver", "AdapterObserverPrx", "_IceGrid_AdapterObserverPrx_t"]
