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

from Ice.StringSeq import _Ice_StringSeq_t

from IceBox.ServiceObserver_forward import _IceBox_ServiceObserverPrx_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from collections.abc import Awaitable
    from collections.abc import Sequence


class ServiceObserverPrx(ObjectPrx):
    """
    Observes the status of services in an IceBox server.
    
    Notes
    -----
        This interface is implemented by admin tools that monitor the IceBox server.
        
        The Slice compiler generated this proxy class from Slice interface ``::IceBox::ServiceObserver``.
    
    See Also
    --------
        :meth:`IceBox.ServiceManagerPrx.addObserverAsync`
    """

    def servicesStarted(self, services: Sequence[str], context: dict[str, str] | None = None) -> None:
        """
        Receives the names of the services that were started.
        
        Parameters
        ----------
        services : Sequence[str]
            The names of the services that were started.
        context : dict[str, str]
            The request context for the invocation.
        """
        return ServiceObserver._op_servicesStarted.invoke(self, ((services, ), context))

    def servicesStartedAsync(self, services: Sequence[str], context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Receives the names of the services that were started.
        
        Parameters
        ----------
        services : Sequence[str]
            The names of the services that were started.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return ServiceObserver._op_servicesStarted.invokeAsync(self, ((services, ), context))

    def servicesStopped(self, services: Sequence[str], context: dict[str, str] | None = None) -> None:
        """
        Receives the names of the services that were stopped.
        
        Parameters
        ----------
        services : Sequence[str]
            The names of the services that were stopped.
        context : dict[str, str]
            The request context for the invocation.
        """
        return ServiceObserver._op_servicesStopped.invoke(self, ((services, ), context))

    def servicesStoppedAsync(self, services: Sequence[str], context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Receives the names of the services that were stopped.
        
        Parameters
        ----------
        services : Sequence[str]
            The names of the services that were stopped.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return ServiceObserver._op_servicesStopped.invokeAsync(self, ((services, ), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> ServiceObserverPrx | None:
        return checkedCast(ServiceObserverPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[ServiceObserverPrx | None ]:
        return checkedCastAsync(ServiceObserverPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> ServiceObserverPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> ServiceObserverPrx | None:
        return uncheckedCast(ServiceObserverPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceBox::ServiceObserver"

IcePy.defineProxy("::IceBox::ServiceObserver", ServiceObserverPrx)

class ServiceObserver(Object, ABC):
    """
    Observes the status of services in an IceBox server.
    
    Notes
    -----
        This interface is implemented by admin tools that monitor the IceBox server.
        
        The Slice compiler generated this skeleton class from Slice interface ``::IceBox::ServiceObserver``.
    
    See Also
    --------
        :meth:`IceBox.ServiceManagerPrx.addObserverAsync`
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::IceBox::ServiceObserver", )
    _op_servicesStarted: IcePy.Operation
    _op_servicesStopped: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceBox::ServiceObserver"

    @abstractmethod
    def servicesStarted(self, services: list[str], current: Current) -> None | Awaitable[None]:
        """
        Receives the names of the services that were started.
        
        Parameters
        ----------
        services : list[str]
            The names of the services that were started.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def servicesStopped(self, services: list[str], current: Current) -> None | Awaitable[None]:
        """
        Receives the names of the services that were stopped.
        
        Parameters
        ----------
        services : list[str]
            The names of the services that were stopped.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

ServiceObserver._op_servicesStarted = IcePy.Operation(
    "servicesStarted",
    "servicesStarted",
    OperationMode.Normal,
    None,
    (),
    (((), _Ice_StringSeq_t, False, 0),),
    (),
    None,
    ())

ServiceObserver._op_servicesStopped = IcePy.Operation(
    "servicesStopped",
    "servicesStopped",
    OperationMode.Normal,
    None,
    (),
    (((), _Ice_StringSeq_t, False, 0),),
    (),
    None,
    ())

__all__ = ["ServiceObserver", "ServiceObserverPrx", "_IceBox_ServiceObserverPrx_t"]
