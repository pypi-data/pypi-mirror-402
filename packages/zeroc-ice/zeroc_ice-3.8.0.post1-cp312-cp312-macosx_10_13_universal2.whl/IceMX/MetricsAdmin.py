# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.FormatType import FormatType

from Ice.Object import Object

from Ice.ObjectPrx import ObjectPrx
from Ice.ObjectPrx import checkedCast
from Ice.ObjectPrx import checkedCastAsync
from Ice.ObjectPrx import uncheckedCast

from Ice.OperationMode import OperationMode

from Ice.StringSeq import _Ice_StringSeq_t

from IceMX.MetricsAdmin_forward import _IceMX_MetricsAdminPrx_t

from IceMX.MetricsFailures import _IceMX_MetricsFailures_t

from IceMX.MetricsFailuresSeq import _IceMX_MetricsFailuresSeq_t

from IceMX.MetricsView import _IceMX_MetricsView_t

from IceMX.UnknownMetricsView import _IceMX_UnknownMetricsView_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from IceMX.Metrics import Metrics
    from IceMX.MetricsFailures import MetricsFailures
    from collections.abc import Awaitable
    from collections.abc import Mapping
    from collections.abc import Sequence


class MetricsAdminPrx(ObjectPrx):
    """
    The metrics administrative facet interface. This interface allows remote administrative clients to access the
    metrics of an application that enabled the Ice administrative facility and configured one or more metrics views.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::IceMX::MetricsAdmin``.
    """

    def getMetricsViewNames(self, context: dict[str, str] | None = None) -> tuple[list[str], list[str]]:
        """
        Gets the names of enabled and disabled metrics.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        tuple[list[str], list[str]]
        
            A tuple containing:
                - list[str] The names of the enabled views.
                - list[str] The names of the disabled views.
        """
        return MetricsAdmin._op_getMetricsViewNames.invoke(self, ((), context))

    def getMetricsViewNamesAsync(self, context: dict[str, str] | None = None) -> Awaitable[tuple[list[str], list[str]]]:
        """
        Gets the names of enabled and disabled metrics.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[tuple[list[str], list[str]]]
        
            A tuple containing:
                - list[str] The names of the enabled views.
                - list[str] The names of the disabled views.
        """
        return MetricsAdmin._op_getMetricsViewNames.invokeAsync(self, ((), context))

    def enableMetricsView(self, name: str, context: dict[str, str] | None = None) -> None:
        """
        Enables a metrics view.
        
        Parameters
        ----------
        name : str
            The metrics view name.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        UnknownMetricsView
            Thrown when the metrics view cannot be found.
        """
        return MetricsAdmin._op_enableMetricsView.invoke(self, ((name, ), context))

    def enableMetricsViewAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Enables a metrics view.
        
        Parameters
        ----------
        name : str
            The metrics view name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return MetricsAdmin._op_enableMetricsView.invokeAsync(self, ((name, ), context))

    def disableMetricsView(self, name: str, context: dict[str, str] | None = None) -> None:
        """
        Disables a metrics view.
        
        Parameters
        ----------
        name : str
            The metrics view name.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        UnknownMetricsView
            Thrown when the metrics view cannot be found.
        """
        return MetricsAdmin._op_disableMetricsView.invoke(self, ((name, ), context))

    def disableMetricsViewAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Disables a metrics view.
        
        Parameters
        ----------
        name : str
            The metrics view name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return MetricsAdmin._op_disableMetricsView.invokeAsync(self, ((name, ), context))

    def getMetricsView(self, view: str, context: dict[str, str] | None = None) -> tuple[dict[str, list[Metrics | None]], int]:
        """
        Gets the metrics objects for the given metrics view.
        
        Parameters
        ----------
        view : str
            The name of the metrics view.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        tuple[dict[str, list[Metrics | None]], int]
        
            A tuple containing:
                - dict[str, list[Metrics | None]] The metrics view data, a dictionary of metric maps for each metrics class configured with the view.
                  The ``timestamp`` allows the client to compute averages which are not dependent of the invocation latency for
                  this operation.
                - int The local time of the process when the metrics objects were retrieved.
        
        Raises
        ------
        UnknownMetricsView
            Thrown when the metrics view cannot be found.
        """
        return MetricsAdmin._op_getMetricsView.invoke(self, ((view, ), context))

    def getMetricsViewAsync(self, view: str, context: dict[str, str] | None = None) -> Awaitable[tuple[dict[str, list[Metrics | None]], int]]:
        """
        Gets the metrics objects for the given metrics view.
        
        Parameters
        ----------
        view : str
            The name of the metrics view.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[tuple[dict[str, list[Metrics | None]], int]]
        
            A tuple containing:
                - dict[str, list[Metrics | None]] The metrics view data, a dictionary of metric maps for each metrics class configured with the view.
                  The ``timestamp`` allows the client to compute averages which are not dependent of the invocation latency for
                  this operation.
                - int The local time of the process when the metrics objects were retrieved.
        """
        return MetricsAdmin._op_getMetricsView.invokeAsync(self, ((view, ), context))

    def getMapMetricsFailures(self, view: str, map: str, context: dict[str, str] | None = None) -> list[MetricsFailures]:
        """
        Gets the metrics failures associated with the given ``view`` and ``map``.
        
        Parameters
        ----------
        view : str
            The name of the metrics view.
        map : str
            The name of the metrics map.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        list[MetricsFailures]
            The metrics failures associated with the map.
        
        Raises
        ------
        UnknownMetricsView
            Thrown when the metrics view cannot be found.
        """
        return MetricsAdmin._op_getMapMetricsFailures.invoke(self, ((view, map), context))

    def getMapMetricsFailuresAsync(self, view: str, map: str, context: dict[str, str] | None = None) -> Awaitable[list[MetricsFailures]]:
        """
        Gets the metrics failures associated with the given ``view`` and ``map``.
        
        Parameters
        ----------
        view : str
            The name of the metrics view.
        map : str
            The name of the metrics map.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[list[MetricsFailures]]
            The metrics failures associated with the map.
        """
        return MetricsAdmin._op_getMapMetricsFailures.invokeAsync(self, ((view, map), context))

    def getMetricsFailures(self, view: str, map: str, id: str, context: dict[str, str] | None = None) -> MetricsFailures:
        """
        Gets the metrics failure associated for the given metrics.
        
        Parameters
        ----------
        view : str
            The name of the metrics view.
        map : str
            The name of the metrics map.
        id : str
            The ID of the metrics.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        MetricsFailures
            The metrics failures associated with the metrics.
        
        Raises
        ------
        UnknownMetricsView
            Thrown when the metrics view cannot be found.
        """
        return MetricsAdmin._op_getMetricsFailures.invoke(self, ((view, map, id), context))

    def getMetricsFailuresAsync(self, view: str, map: str, id: str, context: dict[str, str] | None = None) -> Awaitable[MetricsFailures]:
        """
        Gets the metrics failure associated for the given metrics.
        
        Parameters
        ----------
        view : str
            The name of the metrics view.
        map : str
            The name of the metrics map.
        id : str
            The ID of the metrics.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[MetricsFailures]
            The metrics failures associated with the metrics.
        """
        return MetricsAdmin._op_getMetricsFailures.invokeAsync(self, ((view, map, id), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> MetricsAdminPrx | None:
        return checkedCast(MetricsAdminPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[MetricsAdminPrx | None ]:
        return checkedCastAsync(MetricsAdminPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> MetricsAdminPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> MetricsAdminPrx | None:
        return uncheckedCast(MetricsAdminPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceMX::MetricsAdmin"

IcePy.defineProxy("::IceMX::MetricsAdmin", MetricsAdminPrx)

class MetricsAdmin(Object, ABC):
    """
    The metrics administrative facet interface. This interface allows remote administrative clients to access the
    metrics of an application that enabled the Ice administrative facility and configured one or more metrics views.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::IceMX::MetricsAdmin``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::IceMX::MetricsAdmin", )
    _op_getMetricsViewNames: IcePy.Operation
    _op_enableMetricsView: IcePy.Operation
    _op_disableMetricsView: IcePy.Operation
    _op_getMetricsView: IcePy.Operation
    _op_getMapMetricsFailures: IcePy.Operation
    _op_getMetricsFailures: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceMX::MetricsAdmin"

    @abstractmethod
    def getMetricsViewNames(self, current: Current) -> tuple[Sequence[str], Sequence[str]] | Awaitable[tuple[Sequence[str], Sequence[str]]]:
        """
        Gets the names of enabled and disabled metrics.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        tuple[Sequence[str], Sequence[str]] | Awaitable[tuple[Sequence[str], Sequence[str]]]
        
            A tuple containing:
                - Sequence[str] The names of the enabled views.
                - Sequence[str] The names of the disabled views.
        """
        pass

    @abstractmethod
    def enableMetricsView(self, name: str, current: Current) -> None | Awaitable[None]:
        """
        Enables a metrics view.
        
        Parameters
        ----------
        name : str
            The metrics view name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        UnknownMetricsView
            Thrown when the metrics view cannot be found.
        """
        pass

    @abstractmethod
    def disableMetricsView(self, name: str, current: Current) -> None | Awaitable[None]:
        """
        Disables a metrics view.
        
        Parameters
        ----------
        name : str
            The metrics view name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        UnknownMetricsView
            Thrown when the metrics view cannot be found.
        """
        pass

    @abstractmethod
    def getMetricsView(self, view: str, current: Current) -> tuple[Mapping[str, Sequence[Metrics | None]], int] | Awaitable[tuple[Mapping[str, Sequence[Metrics | None]], int]]:
        """
        Gets the metrics objects for the given metrics view.
        
        Parameters
        ----------
        view : str
            The name of the metrics view.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        tuple[Mapping[str, Sequence[Metrics | None]], int] | Awaitable[tuple[Mapping[str, Sequence[Metrics | None]], int]]
        
            A tuple containing:
                - Mapping[str, Sequence[Metrics | None]] The metrics view data, a dictionary of metric maps for each metrics class configured with the view.
                  The ``timestamp`` allows the client to compute averages which are not dependent of the invocation latency for
                  this operation.
                - int The local time of the process when the metrics objects were retrieved.
        
        Raises
        ------
        UnknownMetricsView
            Thrown when the metrics view cannot be found.
        """
        pass

    @abstractmethod
    def getMapMetricsFailures(self, view: str, map: str, current: Current) -> Sequence[MetricsFailures] | Awaitable[Sequence[MetricsFailures]]:
        """
        Gets the metrics failures associated with the given ``view`` and ``map``.
        
        Parameters
        ----------
        view : str
            The name of the metrics view.
        map : str
            The name of the metrics map.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        Sequence[MetricsFailures] | Awaitable[Sequence[MetricsFailures]]
            The metrics failures associated with the map.
        
        Raises
        ------
        UnknownMetricsView
            Thrown when the metrics view cannot be found.
        """
        pass

    @abstractmethod
    def getMetricsFailures(self, view: str, map: str, id: str, current: Current) -> MetricsFailures | Awaitable[MetricsFailures]:
        """
        Gets the metrics failure associated for the given metrics.
        
        Parameters
        ----------
        view : str
            The name of the metrics view.
        map : str
            The name of the metrics map.
        id : str
            The ID of the metrics.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        MetricsFailures | Awaitable[MetricsFailures]
            The metrics failures associated with the metrics.
        
        Raises
        ------
        UnknownMetricsView
            Thrown when the metrics view cannot be found.
        """
        pass

MetricsAdmin._op_getMetricsViewNames = IcePy.Operation(
    "getMetricsViewNames",
    "getMetricsViewNames",
    OperationMode.Normal,
    None,
    (),
    (),
    (((), _Ice_StringSeq_t, False, 0),),
    ((), _Ice_StringSeq_t, False, 0),
    ())

MetricsAdmin._op_enableMetricsView = IcePy.Operation(
    "enableMetricsView",
    "enableMetricsView",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    None,
    (_IceMX_UnknownMetricsView_t,))

MetricsAdmin._op_disableMetricsView = IcePy.Operation(
    "disableMetricsView",
    "disableMetricsView",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    None,
    (_IceMX_UnknownMetricsView_t,))

MetricsAdmin._op_getMetricsView = IcePy.Operation(
    "getMetricsView",
    "getMetricsView",
    OperationMode.Normal,
    FormatType.SlicedFormat,
    (),
    (((), IcePy._t_string, False, 0),),
    (((), IcePy._t_long, False, 0),),
    ((), _IceMX_MetricsView_t, False, 0),
    (_IceMX_UnknownMetricsView_t,))

MetricsAdmin._op_getMapMetricsFailures = IcePy.Operation(
    "getMapMetricsFailures",
    "getMapMetricsFailures",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0)),
    (),
    ((), _IceMX_MetricsFailuresSeq_t, False, 0),
    (_IceMX_UnknownMetricsView_t,))

MetricsAdmin._op_getMetricsFailures = IcePy.Operation(
    "getMetricsFailures",
    "getMetricsFailures",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0)),
    (),
    ((), _IceMX_MetricsFailures_t, False, 0),
    (_IceMX_UnknownMetricsView_t,))

__all__ = ["MetricsAdmin", "MetricsAdminPrx", "_IceMX_MetricsAdminPrx_t"]
