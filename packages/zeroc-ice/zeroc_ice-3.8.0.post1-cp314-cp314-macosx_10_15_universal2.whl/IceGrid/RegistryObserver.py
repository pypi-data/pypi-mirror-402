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

from IceGrid.RegistryInfo import _IceGrid_RegistryInfo_t

from IceGrid.RegistryInfoSeq import _IceGrid_RegistryInfoSeq_t

from IceGrid.RegistryObserver_forward import _IceGrid_RegistryObserverPrx_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from IceGrid.RegistryInfo import RegistryInfo
    from collections.abc import Awaitable
    from collections.abc import Sequence


class RegistryObserverPrx(ObjectPrx):
    """
    Monitors changes to the state of the registries.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::IceGrid::RegistryObserver``.
    """

    def registryInit(self, registries: Sequence[RegistryInfo], context: dict[str, str] | None = None) -> None:
        """
        Provides the initial state of the registries to the observer.
        
        Parameters
        ----------
        registries : Sequence[RegistryInfo]
            The current state of the registries.
        context : dict[str, str]
            The request context for the invocation.
        """
        return RegistryObserver._op_registryInit.invoke(self, ((registries, ), context))

    def registryInitAsync(self, registries: Sequence[RegistryInfo], context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Provides the initial state of the registries to the observer.
        
        Parameters
        ----------
        registries : Sequence[RegistryInfo]
            The current state of the registries.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return RegistryObserver._op_registryInit.invokeAsync(self, ((registries, ), context))

    def registryUp(self, registryReplica: RegistryInfo, context: dict[str, str] | None = None) -> None:
        """
        Notifies the observer that a registry replica came up.
        
        Parameters
        ----------
        registryReplica : RegistryInfo
            The registry state.
        context : dict[str, str]
            The request context for the invocation.
        """
        return RegistryObserver._op_registryUp.invoke(self, ((registryReplica, ), context))

    def registryUpAsync(self, registryReplica: RegistryInfo, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Notifies the observer that a registry replica came up.
        
        Parameters
        ----------
        registryReplica : RegistryInfo
            The registry state.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return RegistryObserver._op_registryUp.invokeAsync(self, ((registryReplica, ), context))

    def registryDown(self, name: str, context: dict[str, str] | None = None) -> None:
        """
        Notifies the observer that a registry replica went down.
        
        Parameters
        ----------
        name : str
            The registry name.
        context : dict[str, str]
            The request context for the invocation.
        """
        return RegistryObserver._op_registryDown.invoke(self, ((name, ), context))

    def registryDownAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Notifies the observer that a registry replica went down.
        
        Parameters
        ----------
        name : str
            The registry name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return RegistryObserver._op_registryDown.invokeAsync(self, ((name, ), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> RegistryObserverPrx | None:
        return checkedCast(RegistryObserverPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[RegistryObserverPrx | None ]:
        return checkedCastAsync(RegistryObserverPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> RegistryObserverPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> RegistryObserverPrx | None:
        return uncheckedCast(RegistryObserverPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::RegistryObserver"

IcePy.defineProxy("::IceGrid::RegistryObserver", RegistryObserverPrx)

class RegistryObserver(Object, ABC):
    """
    Monitors changes to the state of the registries.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::IceGrid::RegistryObserver``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::IceGrid::RegistryObserver", )
    _op_registryInit: IcePy.Operation
    _op_registryUp: IcePy.Operation
    _op_registryDown: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::RegistryObserver"

    @abstractmethod
    def registryInit(self, registries: list[RegistryInfo], current: Current) -> None | Awaitable[None]:
        """
        Provides the initial state of the registries to the observer.
        
        Parameters
        ----------
        registries : list[RegistryInfo]
            The current state of the registries.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def registryUp(self, registryReplica: RegistryInfo, current: Current) -> None | Awaitable[None]:
        """
        Notifies the observer that a registry replica came up.
        
        Parameters
        ----------
        registryReplica : RegistryInfo
            The registry state.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def registryDown(self, name: str, current: Current) -> None | Awaitable[None]:
        """
        Notifies the observer that a registry replica went down.
        
        Parameters
        ----------
        name : str
            The registry name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

RegistryObserver._op_registryInit = IcePy.Operation(
    "registryInit",
    "registryInit",
    OperationMode.Normal,
    None,
    (),
    (((), _IceGrid_RegistryInfoSeq_t, False, 0),),
    (),
    None,
    ())

RegistryObserver._op_registryUp = IcePy.Operation(
    "registryUp",
    "registryUp",
    OperationMode.Normal,
    None,
    (),
    (((), _IceGrid_RegistryInfo_t, False, 0),),
    (),
    None,
    ())

RegistryObserver._op_registryDown = IcePy.Operation(
    "registryDown",
    "registryDown",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    None,
    ())

__all__ = ["RegistryObserver", "RegistryObserverPrx", "_IceGrid_RegistryObserverPrx_t"]
