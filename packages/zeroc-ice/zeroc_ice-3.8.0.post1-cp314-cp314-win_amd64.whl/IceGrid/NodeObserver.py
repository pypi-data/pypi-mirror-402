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

from IceGrid.AdapterDynamicInfo import _IceGrid_AdapterDynamicInfo_t

from IceGrid.NodeDynamicInfo import _IceGrid_NodeDynamicInfo_t

from IceGrid.NodeDynamicInfoSeq import _IceGrid_NodeDynamicInfoSeq_t

from IceGrid.NodeObserver_forward import _IceGrid_NodeObserverPrx_t

from IceGrid.ServerDynamicInfo import _IceGrid_ServerDynamicInfo_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from IceGrid.AdapterDynamicInfo import AdapterDynamicInfo
    from IceGrid.NodeDynamicInfo import NodeDynamicInfo
    from IceGrid.ServerDynamicInfo import ServerDynamicInfo
    from collections.abc import Awaitable
    from collections.abc import Sequence


class NodeObserverPrx(ObjectPrx):
    """
    Monitors changes to the state of the nodes.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::IceGrid::NodeObserver``.
    """

    def nodeInit(self, nodes: Sequence[NodeDynamicInfo], context: dict[str, str] | None = None) -> None:
        """
        Provides the initial state of the nodes to the observer.
        
        Parameters
        ----------
        nodes : Sequence[NodeDynamicInfo]
            The current state of the nodes.
        context : dict[str, str]
            The request context for the invocation.
        """
        return NodeObserver._op_nodeInit.invoke(self, ((nodes, ), context))

    def nodeInitAsync(self, nodes: Sequence[NodeDynamicInfo], context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Provides the initial state of the nodes to the observer.
        
        Parameters
        ----------
        nodes : Sequence[NodeDynamicInfo]
            The current state of the nodes.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return NodeObserver._op_nodeInit.invokeAsync(self, ((nodes, ), context))

    def nodeUp(self, node: NodeDynamicInfo, context: dict[str, str] | None = None) -> None:
        """
        Notifies the observer that a node came up.
        
        Parameters
        ----------
        node : NodeDynamicInfo
            The node state.
        context : dict[str, str]
            The request context for the invocation.
        """
        return NodeObserver._op_nodeUp.invoke(self, ((node, ), context))

    def nodeUpAsync(self, node: NodeDynamicInfo, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Notifies the observer that a node came up.
        
        Parameters
        ----------
        node : NodeDynamicInfo
            The node state.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return NodeObserver._op_nodeUp.invokeAsync(self, ((node, ), context))

    def nodeDown(self, name: str, context: dict[str, str] | None = None) -> None:
        """
        Notifies the observer that a node went down.
        
        Parameters
        ----------
        name : str
            The node name.
        context : dict[str, str]
            The request context for the invocation.
        """
        return NodeObserver._op_nodeDown.invoke(self, ((name, ), context))

    def nodeDownAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Notifies the observer that a node went down.
        
        Parameters
        ----------
        name : str
            The node name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return NodeObserver._op_nodeDown.invokeAsync(self, ((name, ), context))

    def updateServer(self, node: str, updatedInfo: ServerDynamicInfo, context: dict[str, str] | None = None) -> None:
        """
        Notifies the observer that the state of a server changed.
        
        Parameters
        ----------
        node : str
            The node hosting the server.
        updatedInfo : ServerDynamicInfo
            The new server state.
        context : dict[str, str]
            The request context for the invocation.
        """
        return NodeObserver._op_updateServer.invoke(self, ((node, updatedInfo), context))

    def updateServerAsync(self, node: str, updatedInfo: ServerDynamicInfo, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Notifies the observer that the state of a server changed.
        
        Parameters
        ----------
        node : str
            The node hosting the server.
        updatedInfo : ServerDynamicInfo
            The new server state.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return NodeObserver._op_updateServer.invokeAsync(self, ((node, updatedInfo), context))

    def updateAdapter(self, node: str, updatedInfo: AdapterDynamicInfo, context: dict[str, str] | None = None) -> None:
        """
        Notifies the observer that the state of an object adapter changed.
        
        Parameters
        ----------
        node : str
            The node hosting the adapter.
        updatedInfo : AdapterDynamicInfo
            The new adapter state.
        context : dict[str, str]
            The request context for the invocation.
        """
        return NodeObserver._op_updateAdapter.invoke(self, ((node, updatedInfo), context))

    def updateAdapterAsync(self, node: str, updatedInfo: AdapterDynamicInfo, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Notifies the observer that the state of an object adapter changed.
        
        Parameters
        ----------
        node : str
            The node hosting the adapter.
        updatedInfo : AdapterDynamicInfo
            The new adapter state.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return NodeObserver._op_updateAdapter.invokeAsync(self, ((node, updatedInfo), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> NodeObserverPrx | None:
        return checkedCast(NodeObserverPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[NodeObserverPrx | None ]:
        return checkedCastAsync(NodeObserverPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> NodeObserverPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> NodeObserverPrx | None:
        return uncheckedCast(NodeObserverPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::NodeObserver"

IcePy.defineProxy("::IceGrid::NodeObserver", NodeObserverPrx)

class NodeObserver(Object, ABC):
    """
    Monitors changes to the state of the nodes.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::IceGrid::NodeObserver``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::IceGrid::NodeObserver", )
    _op_nodeInit: IcePy.Operation
    _op_nodeUp: IcePy.Operation
    _op_nodeDown: IcePy.Operation
    _op_updateServer: IcePy.Operation
    _op_updateAdapter: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::NodeObserver"

    @abstractmethod
    def nodeInit(self, nodes: list[NodeDynamicInfo], current: Current) -> None | Awaitable[None]:
        """
        Provides the initial state of the nodes to the observer.
        
        Parameters
        ----------
        nodes : list[NodeDynamicInfo]
            The current state of the nodes.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def nodeUp(self, node: NodeDynamicInfo, current: Current) -> None | Awaitable[None]:
        """
        Notifies the observer that a node came up.
        
        Parameters
        ----------
        node : NodeDynamicInfo
            The node state.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def nodeDown(self, name: str, current: Current) -> None | Awaitable[None]:
        """
        Notifies the observer that a node went down.
        
        Parameters
        ----------
        name : str
            The node name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def updateServer(self, node: str, updatedInfo: ServerDynamicInfo, current: Current) -> None | Awaitable[None]:
        """
        Notifies the observer that the state of a server changed.
        
        Parameters
        ----------
        node : str
            The node hosting the server.
        updatedInfo : ServerDynamicInfo
            The new server state.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def updateAdapter(self, node: str, updatedInfo: AdapterDynamicInfo, current: Current) -> None | Awaitable[None]:
        """
        Notifies the observer that the state of an object adapter changed.
        
        Parameters
        ----------
        node : str
            The node hosting the adapter.
        updatedInfo : AdapterDynamicInfo
            The new adapter state.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

NodeObserver._op_nodeInit = IcePy.Operation(
    "nodeInit",
    "nodeInit",
    OperationMode.Normal,
    None,
    (),
    (((), _IceGrid_NodeDynamicInfoSeq_t, False, 0),),
    (),
    None,
    ())

NodeObserver._op_nodeUp = IcePy.Operation(
    "nodeUp",
    "nodeUp",
    OperationMode.Normal,
    None,
    (),
    (((), _IceGrid_NodeDynamicInfo_t, False, 0),),
    (),
    None,
    ())

NodeObserver._op_nodeDown = IcePy.Operation(
    "nodeDown",
    "nodeDown",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    None,
    ())

NodeObserver._op_updateServer = IcePy.Operation(
    "updateServer",
    "updateServer",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), _IceGrid_ServerDynamicInfo_t, False, 0)),
    (),
    None,
    ())

NodeObserver._op_updateAdapter = IcePy.Operation(
    "updateAdapter",
    "updateAdapter",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), _IceGrid_AdapterDynamicInfo_t, False, 0)),
    (),
    None,
    ())

__all__ = ["NodeObserver", "NodeObserverPrx", "_IceGrid_NodeObserverPrx_t"]
