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

from IceGrid.ApplicationInfo import _IceGrid_ApplicationInfo_t

from IceGrid.ApplicationInfoSeq import _IceGrid_ApplicationInfoSeq_t

from IceGrid.ApplicationObserver_forward import _IceGrid_ApplicationObserverPrx_t

from IceGrid.ApplicationUpdateInfo import _IceGrid_ApplicationUpdateInfo_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from IceGrid.ApplicationInfo import ApplicationInfo
    from IceGrid.ApplicationUpdateInfo import ApplicationUpdateInfo
    from collections.abc import Awaitable
    from collections.abc import Sequence


class ApplicationObserverPrx(ObjectPrx):
    """
    Monitors applications.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::IceGrid::ApplicationObserver``.
    """

    def applicationInit(self, serial: int, applications: Sequence[ApplicationInfo], context: dict[str, str] | None = None) -> None:
        """
        Provides the initial application infos to the observer.
        
        Parameters
        ----------
        serial : int
            The current serial number of the registry database. This serial number allows observers to
            make sure that their internal state is synchronized with the registry.
        applications : Sequence[ApplicationInfo]
            The applications currently registered with the registry.
        context : dict[str, str]
            The request context for the invocation.
        """
        return ApplicationObserver._op_applicationInit.invoke(self, ((serial, applications), context))

    def applicationInitAsync(self, serial: int, applications: Sequence[ApplicationInfo], context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Provides the initial application infos to the observer.
        
        Parameters
        ----------
        serial : int
            The current serial number of the registry database. This serial number allows observers to
            make sure that their internal state is synchronized with the registry.
        applications : Sequence[ApplicationInfo]
            The applications currently registered with the registry.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return ApplicationObserver._op_applicationInit.invokeAsync(self, ((serial, applications), context))

    def applicationAdded(self, serial: int, desc: ApplicationInfo, context: dict[str, str] | None = None) -> None:
        """
        Notifies the observer that an application was added.
        
        Parameters
        ----------
        serial : int
            The new serial number of the registry database.
        desc : ApplicationInfo
            The descriptor of the new application.
        context : dict[str, str]
            The request context for the invocation.
        """
        return ApplicationObserver._op_applicationAdded.invoke(self, ((serial, desc), context))

    def applicationAddedAsync(self, serial: int, desc: ApplicationInfo, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Notifies the observer that an application was added.
        
        Parameters
        ----------
        serial : int
            The new serial number of the registry database.
        desc : ApplicationInfo
            The descriptor of the new application.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return ApplicationObserver._op_applicationAdded.invokeAsync(self, ((serial, desc), context))

    def applicationRemoved(self, serial: int, name: str, context: dict[str, str] | None = None) -> None:
        """
        Notifies the observer that an application was removed.
        
        Parameters
        ----------
        serial : int
            The new serial number of the registry database.
        name : str
            The name of the application that was removed.
        context : dict[str, str]
            The request context for the invocation.
        """
        return ApplicationObserver._op_applicationRemoved.invoke(self, ((serial, name), context))

    def applicationRemovedAsync(self, serial: int, name: str, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Notifies the observer that an application was removed.
        
        Parameters
        ----------
        serial : int
            The new serial number of the registry database.
        name : str
            The name of the application that was removed.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return ApplicationObserver._op_applicationRemoved.invokeAsync(self, ((serial, name), context))

    def applicationUpdated(self, serial: int, desc: ApplicationUpdateInfo, context: dict[str, str] | None = None) -> None:
        """
        Notifies the observer that an application was updated.
        
        Parameters
        ----------
        serial : int
            The new serial number of the registry database.
        desc : ApplicationUpdateInfo
            The descriptor of the update.
        context : dict[str, str]
            The request context for the invocation.
        """
        return ApplicationObserver._op_applicationUpdated.invoke(self, ((serial, desc), context))

    def applicationUpdatedAsync(self, serial: int, desc: ApplicationUpdateInfo, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Notifies the observer that an application was updated.
        
        Parameters
        ----------
        serial : int
            The new serial number of the registry database.
        desc : ApplicationUpdateInfo
            The descriptor of the update.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return ApplicationObserver._op_applicationUpdated.invokeAsync(self, ((serial, desc), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> ApplicationObserverPrx | None:
        return checkedCast(ApplicationObserverPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[ApplicationObserverPrx | None ]:
        return checkedCastAsync(ApplicationObserverPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> ApplicationObserverPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> ApplicationObserverPrx | None:
        return uncheckedCast(ApplicationObserverPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::ApplicationObserver"

IcePy.defineProxy("::IceGrid::ApplicationObserver", ApplicationObserverPrx)

class ApplicationObserver(Object, ABC):
    """
    Monitors applications.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::IceGrid::ApplicationObserver``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::IceGrid::ApplicationObserver", )
    _op_applicationInit: IcePy.Operation
    _op_applicationAdded: IcePy.Operation
    _op_applicationRemoved: IcePy.Operation
    _op_applicationUpdated: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::ApplicationObserver"

    @abstractmethod
    def applicationInit(self, serial: int, applications: list[ApplicationInfo], current: Current) -> None | Awaitable[None]:
        """
        Provides the initial application infos to the observer.
        
        Parameters
        ----------
        serial : int
            The current serial number of the registry database. This serial number allows observers to
            make sure that their internal state is synchronized with the registry.
        applications : list[ApplicationInfo]
            The applications currently registered with the registry.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def applicationAdded(self, serial: int, desc: ApplicationInfo, current: Current) -> None | Awaitable[None]:
        """
        Notifies the observer that an application was added.
        
        Parameters
        ----------
        serial : int
            The new serial number of the registry database.
        desc : ApplicationInfo
            The descriptor of the new application.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def applicationRemoved(self, serial: int, name: str, current: Current) -> None | Awaitable[None]:
        """
        Notifies the observer that an application was removed.
        
        Parameters
        ----------
        serial : int
            The new serial number of the registry database.
        name : str
            The name of the application that was removed.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def applicationUpdated(self, serial: int, desc: ApplicationUpdateInfo, current: Current) -> None | Awaitable[None]:
        """
        Notifies the observer that an application was updated.
        
        Parameters
        ----------
        serial : int
            The new serial number of the registry database.
        desc : ApplicationUpdateInfo
            The descriptor of the update.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

ApplicationObserver._op_applicationInit = IcePy.Operation(
    "applicationInit",
    "applicationInit",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_int, False, 0), ((), _IceGrid_ApplicationInfoSeq_t, False, 0)),
    (),
    None,
    ())

ApplicationObserver._op_applicationAdded = IcePy.Operation(
    "applicationAdded",
    "applicationAdded",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_int, False, 0), ((), _IceGrid_ApplicationInfo_t, False, 0)),
    (),
    None,
    ())

ApplicationObserver._op_applicationRemoved = IcePy.Operation(
    "applicationRemoved",
    "applicationRemoved",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_int, False, 0), ((), IcePy._t_string, False, 0)),
    (),
    None,
    ())

ApplicationObserver._op_applicationUpdated = IcePy.Operation(
    "applicationUpdated",
    "applicationUpdated",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_int, False, 0), ((), _IceGrid_ApplicationUpdateInfo_t, False, 0)),
    (),
    None,
    ())

__all__ = ["ApplicationObserver", "ApplicationObserverPrx", "_IceGrid_ApplicationObserverPrx_t"]
