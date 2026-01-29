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

from IceStorm.NoSuchTopic import _IceStorm_NoSuchTopic_t

from IceStorm.TopicDict import _IceStorm_TopicDict_t

from IceStorm.TopicExists import _IceStorm_TopicExists_t

from IceStorm.TopicManager_forward import _IceStorm_TopicManagerPrx_t

from IceStorm.Topic_forward import _IceStorm_TopicPrx_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from IceStorm.Topic import TopicPrx
    from collections.abc import Awaitable
    from collections.abc import Mapping
    from collections.abc import Sequence


class TopicManagerPrx(ObjectPrx):
    """
    Represents an object that manages topics.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::IceStorm::TopicManager``.
    
    See Also
    --------
        :class:`IceStorm.TopicPrx`
    """

    def create(self, name: str, context: dict[str, str] | None = None) -> TopicPrx | None:
        """
        Creates a new topic.
        
        Parameters
        ----------
        name : str
            The name of the topic.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        TopicPrx | None
            A proxy to the new topic object. The returned proxy is never null.
        
        Raises
        ------
        TopicExists
            Thrown when a topic with the same ``name`` already exists.
        """
        return TopicManager._op_create.invoke(self, ((name, ), context))

    def createAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[TopicPrx | None]:
        """
        Creates a new topic.
        
        Parameters
        ----------
        name : str
            The name of the topic.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[TopicPrx | None]
            A proxy to the new topic object. The returned proxy is never null.
        """
        return TopicManager._op_create.invokeAsync(self, ((name, ), context))

    def retrieve(self, name: str, context: dict[str, str] | None = None) -> TopicPrx | None:
        """
        Retrieves a topic by name.
        
        Parameters
        ----------
        name : str
            The name of the topic.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        TopicPrx | None
            A proxy to the topic object. The returned proxy is never null.
        
        Raises
        ------
        NoSuchTopic
            Thrown when there is no topic named ``name``.
        """
        return TopicManager._op_retrieve.invoke(self, ((name, ), context))

    def retrieveAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[TopicPrx | None]:
        """
        Retrieves a topic by name.
        
        Parameters
        ----------
        name : str
            The name of the topic.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[TopicPrx | None]
            A proxy to the topic object. The returned proxy is never null.
        """
        return TopicManager._op_retrieve.invokeAsync(self, ((name, ), context))

    def createOrRetrieve(self, name: str, context: dict[str, str] | None = None) -> TopicPrx | None:
        """
        Creates a new topic with the given name, or retrieves the existing topic with this name if it already
        exists.
        
        Parameters
        ----------
        name : str
            The name of the topic.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        TopicPrx | None
            A proxy to the topic object. The returned proxy is never null.
        """
        return TopicManager._op_createOrRetrieve.invoke(self, ((name, ), context))

    def createOrRetrieveAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[TopicPrx | None]:
        """
        Creates a new topic with the given name, or retrieves the existing topic with this name if it already
        exists.
        
        Parameters
        ----------
        name : str
            The name of the topic.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[TopicPrx | None]
            A proxy to the topic object. The returned proxy is never null.
        """
        return TopicManager._op_createOrRetrieve.invokeAsync(self, ((name, ), context))

    def retrieveAll(self, context: dict[str, str] | None = None) -> dict[str, TopicPrx | None]:
        """
        Retrieves all topics managed by this topic manager.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        dict[str, TopicPrx | None]
            A dictionary of string, topic proxy pairs.
        """
        return TopicManager._op_retrieveAll.invoke(self, ((), context))

    def retrieveAllAsync(self, context: dict[str, str] | None = None) -> Awaitable[dict[str, TopicPrx | None]]:
        """
        Retrieves all topics managed by this topic manager.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[dict[str, TopicPrx | None]]
            A dictionary of string, topic proxy pairs.
        """
        return TopicManager._op_retrieveAll.invokeAsync(self, ((), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> TopicManagerPrx | None:
        return checkedCast(TopicManagerPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[TopicManagerPrx | None ]:
        return checkedCastAsync(TopicManagerPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> TopicManagerPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> TopicManagerPrx | None:
        return uncheckedCast(TopicManagerPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceStorm::TopicManager"

IcePy.defineProxy("::IceStorm::TopicManager", TopicManagerPrx)

class TopicManager(Object, ABC):
    """
    Represents an object that manages topics.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::IceStorm::TopicManager``.
    
    See Also
    --------
        :class:`IceStorm.TopicPrx`
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::IceStorm::TopicManager", )
    _op_create: IcePy.Operation
    _op_retrieve: IcePy.Operation
    _op_createOrRetrieve: IcePy.Operation
    _op_retrieveAll: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceStorm::TopicManager"

    @abstractmethod
    def create(self, name: str, current: Current) -> TopicPrx | None | Awaitable[TopicPrx | None]:
        """
        Creates a new topic.
        
        Parameters
        ----------
        name : str
            The name of the topic.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        TopicPrx | None | Awaitable[TopicPrx | None]
            A proxy to the new topic object. The returned proxy is never null.
        
        Raises
        ------
        TopicExists
            Thrown when a topic with the same ``name`` already exists.
        """
        pass

    @abstractmethod
    def retrieve(self, name: str, current: Current) -> TopicPrx | None | Awaitable[TopicPrx | None]:
        """
        Retrieves a topic by name.
        
        Parameters
        ----------
        name : str
            The name of the topic.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        TopicPrx | None | Awaitable[TopicPrx | None]
            A proxy to the topic object. The returned proxy is never null.
        
        Raises
        ------
        NoSuchTopic
            Thrown when there is no topic named ``name``.
        """
        pass

    @abstractmethod
    def createOrRetrieve(self, name: str, current: Current) -> TopicPrx | None | Awaitable[TopicPrx | None]:
        """
        Creates a new topic with the given name, or retrieves the existing topic with this name if it already
        exists.
        
        Parameters
        ----------
        name : str
            The name of the topic.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        TopicPrx | None | Awaitable[TopicPrx | None]
            A proxy to the topic object. The returned proxy is never null.
        """
        pass

    @abstractmethod
    def retrieveAll(self, current: Current) -> Mapping[str, TopicPrx | None] | Awaitable[Mapping[str, TopicPrx | None]]:
        """
        Retrieves all topics managed by this topic manager.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        Mapping[str, TopicPrx | None] | Awaitable[Mapping[str, TopicPrx | None]]
            A dictionary of string, topic proxy pairs.
        """
        pass

TopicManager._op_create = IcePy.Operation(
    "create",
    "create",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _IceStorm_TopicPrx_t, False, 0),
    (_IceStorm_TopicExists_t,))

TopicManager._op_retrieve = IcePy.Operation(
    "retrieve",
    "retrieve",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _IceStorm_TopicPrx_t, False, 0),
    (_IceStorm_NoSuchTopic_t,))

TopicManager._op_createOrRetrieve = IcePy.Operation(
    "createOrRetrieve",
    "createOrRetrieve",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _IceStorm_TopicPrx_t, False, 0),
    ())

TopicManager._op_retrieveAll = IcePy.Operation(
    "retrieveAll",
    "retrieveAll",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), _IceStorm_TopicDict_t, False, 0),
    ())

__all__ = ["TopicManager", "TopicManagerPrx", "_IceStorm_TopicManagerPrx_t"]
