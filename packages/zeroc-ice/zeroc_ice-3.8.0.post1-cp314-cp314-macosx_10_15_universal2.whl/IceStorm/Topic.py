# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.IdentitySeq import _Ice_IdentitySeq_t

from Ice.Object import Object

from Ice.ObjectPrx import ObjectPrx
from Ice.ObjectPrx import checkedCast
from Ice.ObjectPrx import checkedCastAsync
from Ice.ObjectPrx import uncheckedCast

from Ice.ObjectPrx_forward import _Ice_ObjectPrx_t

from Ice.OperationMode import OperationMode

from IceStorm.AlreadySubscribed import _IceStorm_AlreadySubscribed_t

from IceStorm.BadQoS import _IceStorm_BadQoS_t

from IceStorm.LinkExists import _IceStorm_LinkExists_t

from IceStorm.LinkInfoSeq import _IceStorm_LinkInfoSeq_t

from IceStorm.NoSuchLink import _IceStorm_NoSuchLink_t

from IceStorm.QoS import _IceStorm_QoS_t

from IceStorm.Topic_forward import _IceStorm_TopicPrx_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from Ice.Identity import Identity
    from IceStorm.LinkInfo import LinkInfo
    from collections.abc import Awaitable
    from collections.abc import Mapping
    from collections.abc import Sequence


class TopicPrx(ObjectPrx):
    """
    Represents an IceStorm topic. Publishers publish data to a topic (via the topic's publisher object), and
    subscribers subscribe to a topic.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::IceStorm::Topic``.
    
    See Also
    --------
        :class:`IceStorm.TopicManagerPrx`
    """

    def getName(self, context: dict[str, str] | None = None) -> str:
        """
        Gets the name of this topic.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        str
            The name of the topic.
        
        See Also
        --------
            :meth:`IceStorm.TopicManagerPrx.createAsync`
        """
        return Topic._op_getName.invoke(self, ((), context))

    def getNameAsync(self, context: dict[str, str] | None = None) -> Awaitable[str]:
        """
        Gets the name of this topic.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[str]
            The name of the topic.
        
        See Also
        --------
            :meth:`IceStorm.TopicManagerPrx.createAsync`
        """
        return Topic._op_getName.invokeAsync(self, ((), context))

    def getPublisher(self, context: dict[str, str] | None = None) -> ObjectPrx | None:
        """
        Gets a proxy to a publisher object for this topic. To publish data to a topic, a publisher calls this
        operation and then creates a proxy with the publisher type from this proxy. If a replicated IceStorm
        deployment is used, this call may return a replicated proxy.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ObjectPrx | None
            A proxy to publish data on this topic. This proxy is never null.
        """
        return Topic._op_getPublisher.invoke(self, ((), context))

    def getPublisherAsync(self, context: dict[str, str] | None = None) -> Awaitable[ObjectPrx | None]:
        """
        Gets a proxy to a publisher object for this topic. To publish data to a topic, a publisher calls this
        operation and then creates a proxy with the publisher type from this proxy. If a replicated IceStorm
        deployment is used, this call may return a replicated proxy.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ObjectPrx | None]
            A proxy to publish data on this topic. This proxy is never null.
        """
        return Topic._op_getPublisher.invokeAsync(self, ((), context))

    def getNonReplicatedPublisher(self, context: dict[str, str] | None = None) -> ObjectPrx | None:
        """
        Gets a non-replicated proxy to a publisher object for this topic. To publish data to a topic, a publisher
        calls this operation and then creates a proxy with the publisher type from this proxy.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ObjectPrx | None
            A proxy to publish data on this topic. This proxy is never null.
        """
        return Topic._op_getNonReplicatedPublisher.invoke(self, ((), context))

    def getNonReplicatedPublisherAsync(self, context: dict[str, str] | None = None) -> Awaitable[ObjectPrx | None]:
        """
        Gets a non-replicated proxy to a publisher object for this topic. To publish data to a topic, a publisher
        calls this operation and then creates a proxy with the publisher type from this proxy.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ObjectPrx | None]
            A proxy to publish data on this topic. This proxy is never null.
        """
        return Topic._op_getNonReplicatedPublisher.invokeAsync(self, ((), context))

    def subscribeAndGetPublisher(self, theQoS: Mapping[str, str], subscriber: ObjectPrx | None, context: dict[str, str] | None = None) -> ObjectPrx | None:
        """
        Subscribes to this topic.
        
        Parameters
        ----------
        theQoS : Mapping[str, str]
            The quality of service parameters for this subscription.
        subscriber : ObjectPrx | None
            The subscriber's proxy. This proxy cannot be null.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ObjectPrx | None
            The per-subscriber publisher proxy. This proxy is never null.
        
        Raises
        ------
        AlreadySubscribed
            Thrown when ``subscriber`` is already subscribed.
        BadQoS
            Thrown when ``theQoS`` is unavailable or invalid.
        
        See Also
        --------
            :meth:`IceStorm.TopicPrx.unsubscribeAsync`
        """
        return Topic._op_subscribeAndGetPublisher.invoke(self, ((theQoS, subscriber), context))

    def subscribeAndGetPublisherAsync(self, theQoS: Mapping[str, str], subscriber: ObjectPrx | None, context: dict[str, str] | None = None) -> Awaitable[ObjectPrx | None]:
        """
        Subscribes to this topic.
        
        Parameters
        ----------
        theQoS : Mapping[str, str]
            The quality of service parameters for this subscription.
        subscriber : ObjectPrx | None
            The subscriber's proxy. This proxy cannot be null.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ObjectPrx | None]
            The per-subscriber publisher proxy. This proxy is never null.
        
        See Also
        --------
            :meth:`IceStorm.TopicPrx.unsubscribeAsync`
        """
        return Topic._op_subscribeAndGetPublisher.invokeAsync(self, ((theQoS, subscriber), context))

    def unsubscribe(self, subscriber: ObjectPrx | None, context: dict[str, str] | None = None) -> None:
        """
        Unsubscribes the provided ``subscriber`` from this topic.
        
        Parameters
        ----------
        subscriber : ObjectPrx | None
            A proxy to an existing subscriber. This proxy is never null.
        context : dict[str, str]
            The request context for the invocation.
        
        See Also
        --------
            :meth:`IceStorm.TopicPrx.subscribeAndGetPublisherAsync`
        """
        return Topic._op_unsubscribe.invoke(self, ((subscriber, ), context))

    def unsubscribeAsync(self, subscriber: ObjectPrx | None, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Unsubscribes the provided ``subscriber`` from this topic.
        
        Parameters
        ----------
        subscriber : ObjectPrx | None
            A proxy to an existing subscriber. This proxy is never null.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        
        See Also
        --------
            :meth:`IceStorm.TopicPrx.subscribeAndGetPublisherAsync`
        """
        return Topic._op_unsubscribe.invokeAsync(self, ((subscriber, ), context))

    def link(self, linkTo: TopicPrx | None, cost: int, context: dict[str, str] | None = None) -> None:
        """
        Creates a link to another topic. All events originating on this topic will also be sent to the other topic.
        
        Parameters
        ----------
        linkTo : TopicPrx | None
            The topic to link to. This proxy cannot be null.
        cost : int
            The cost of the link.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        LinkExists
            Thrown when a link to ``linkTo`` already exists.
        """
        return Topic._op_link.invoke(self, ((linkTo, cost), context))

    def linkAsync(self, linkTo: TopicPrx | None, cost: int, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Creates a link to another topic. All events originating on this topic will also be sent to the other topic.
        
        Parameters
        ----------
        linkTo : TopicPrx | None
            The topic to link to. This proxy cannot be null.
        cost : int
            The cost of the link.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Topic._op_link.invokeAsync(self, ((linkTo, cost), context))

    def unlink(self, linkTo: TopicPrx | None, context: dict[str, str] | None = None) -> None:
        """
        Destroys a link from this topic to the provided topic.
        
        Parameters
        ----------
        linkTo : TopicPrx | None
            The topic to destroy the link to. This proxy cannot be null.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        NoSuchLink
            Thrown when a link to ``linkTo`` does not exist.
        """
        return Topic._op_unlink.invoke(self, ((linkTo, ), context))

    def unlinkAsync(self, linkTo: TopicPrx | None, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Destroys a link from this topic to the provided topic.
        
        Parameters
        ----------
        linkTo : TopicPrx | None
            The topic to destroy the link to. This proxy cannot be null.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Topic._op_unlink.invokeAsync(self, ((linkTo, ), context))

    def getLinkInfoSeq(self, context: dict[str, str] | None = None) -> list[LinkInfo]:
        """
        Gets information on the current links.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        list[LinkInfo]
            A sequence of LinkInfo objects.
        """
        return Topic._op_getLinkInfoSeq.invoke(self, ((), context))

    def getLinkInfoSeqAsync(self, context: dict[str, str] | None = None) -> Awaitable[list[LinkInfo]]:
        """
        Gets information on the current links.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[list[LinkInfo]]
            A sequence of LinkInfo objects.
        """
        return Topic._op_getLinkInfoSeq.invokeAsync(self, ((), context))

    def getSubscribers(self, context: dict[str, str] | None = None) -> list[Identity]:
        """
        Gets the list of subscribers for this topic.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        list[Identity]
            The sequence of Ice identities for the subscriber objects.
        """
        return Topic._op_getSubscribers.invoke(self, ((), context))

    def getSubscribersAsync(self, context: dict[str, str] | None = None) -> Awaitable[list[Identity]]:
        """
        Gets the list of subscribers for this topic.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[list[Identity]]
            The sequence of Ice identities for the subscriber objects.
        """
        return Topic._op_getSubscribers.invokeAsync(self, ((), context))

    def destroy(self, context: dict[str, str] | None = None) -> None:
        """
        Destroys this topic.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        """
        return Topic._op_destroy.invoke(self, ((), context))

    def destroyAsync(self, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Destroys this topic.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Topic._op_destroy.invokeAsync(self, ((), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> TopicPrx | None:
        return checkedCast(TopicPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[TopicPrx | None ]:
        return checkedCastAsync(TopicPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> TopicPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> TopicPrx | None:
        return uncheckedCast(TopicPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceStorm::Topic"

IcePy.defineProxy("::IceStorm::Topic", TopicPrx)

class Topic(Object, ABC):
    """
    Represents an IceStorm topic. Publishers publish data to a topic (via the topic's publisher object), and
    subscribers subscribe to a topic.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::IceStorm::Topic``.
    
    See Also
    --------
        :class:`IceStorm.TopicManagerPrx`
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::IceStorm::Topic", )
    _op_getName: IcePy.Operation
    _op_getPublisher: IcePy.Operation
    _op_getNonReplicatedPublisher: IcePy.Operation
    _op_subscribeAndGetPublisher: IcePy.Operation
    _op_unsubscribe: IcePy.Operation
    _op_link: IcePy.Operation
    _op_unlink: IcePy.Operation
    _op_getLinkInfoSeq: IcePy.Operation
    _op_getSubscribers: IcePy.Operation
    _op_destroy: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceStorm::Topic"

    @abstractmethod
    def getName(self, current: Current) -> str | Awaitable[str]:
        """
        Gets the name of this topic.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        str | Awaitable[str]
            The name of the topic.
        
        See Also
        --------
            :meth:`IceStorm.TopicManagerPrx.createAsync`
        """
        pass

    @abstractmethod
    def getPublisher(self, current: Current) -> ObjectPrx | None | Awaitable[ObjectPrx | None]:
        """
        Gets a proxy to a publisher object for this topic. To publish data to a topic, a publisher calls this
        operation and then creates a proxy with the publisher type from this proxy. If a replicated IceStorm
        deployment is used, this call may return a replicated proxy.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ObjectPrx | None | Awaitable[ObjectPrx | None]
            A proxy to publish data on this topic. This proxy is never null.
        """
        pass

    @abstractmethod
    def getNonReplicatedPublisher(self, current: Current) -> ObjectPrx | None | Awaitable[ObjectPrx | None]:
        """
        Gets a non-replicated proxy to a publisher object for this topic. To publish data to a topic, a publisher
        calls this operation and then creates a proxy with the publisher type from this proxy.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ObjectPrx | None | Awaitable[ObjectPrx | None]
            A proxy to publish data on this topic. This proxy is never null.
        """
        pass

    @abstractmethod
    def subscribeAndGetPublisher(self, theQoS: dict[str, str], subscriber: ObjectPrx | None, current: Current) -> ObjectPrx | None | Awaitable[ObjectPrx | None]:
        """
        Subscribes to this topic.
        
        Parameters
        ----------
        theQoS : dict[str, str]
            The quality of service parameters for this subscription.
        subscriber : ObjectPrx | None
            The subscriber's proxy. This proxy cannot be null.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ObjectPrx | None | Awaitable[ObjectPrx | None]
            The per-subscriber publisher proxy. This proxy is never null.
        
        Raises
        ------
        AlreadySubscribed
            Thrown when ``subscriber`` is already subscribed.
        BadQoS
            Thrown when ``theQoS`` is unavailable or invalid.
        
        See Also
        --------
            :meth:`IceStorm.TopicPrx.unsubscribeAsync`
        """
        pass

    @abstractmethod
    def unsubscribe(self, subscriber: ObjectPrx | None, current: Current) -> None | Awaitable[None]:
        """
        Unsubscribes the provided ``subscriber`` from this topic.
        
        Parameters
        ----------
        subscriber : ObjectPrx | None
            A proxy to an existing subscriber. This proxy is never null.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        See Also
        --------
            :meth:`IceStorm.TopicPrx.subscribeAndGetPublisherAsync`
        """
        pass

    @abstractmethod
    def link(self, linkTo: TopicPrx | None, cost: int, current: Current) -> None | Awaitable[None]:
        """
        Creates a link to another topic. All events originating on this topic will also be sent to the other topic.
        
        Parameters
        ----------
        linkTo : TopicPrx | None
            The topic to link to. This proxy cannot be null.
        cost : int
            The cost of the link.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        LinkExists
            Thrown when a link to ``linkTo`` already exists.
        """
        pass

    @abstractmethod
    def unlink(self, linkTo: TopicPrx | None, current: Current) -> None | Awaitable[None]:
        """
        Destroys a link from this topic to the provided topic.
        
        Parameters
        ----------
        linkTo : TopicPrx | None
            The topic to destroy the link to. This proxy cannot be null.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        NoSuchLink
            Thrown when a link to ``linkTo`` does not exist.
        """
        pass

    @abstractmethod
    def getLinkInfoSeq(self, current: Current) -> Sequence[LinkInfo] | Awaitable[Sequence[LinkInfo]]:
        """
        Gets information on the current links.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        Sequence[LinkInfo] | Awaitable[Sequence[LinkInfo]]
            A sequence of LinkInfo objects.
        """
        pass

    @abstractmethod
    def getSubscribers(self, current: Current) -> Sequence[Identity] | Awaitable[Sequence[Identity]]:
        """
        Gets the list of subscribers for this topic.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        Sequence[Identity] | Awaitable[Sequence[Identity]]
            The sequence of Ice identities for the subscriber objects.
        """
        pass

    @abstractmethod
    def destroy(self, current: Current) -> None | Awaitable[None]:
        """
        Destroys this topic.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

Topic._op_getName = IcePy.Operation(
    "getName",
    "getName",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), IcePy._t_string, False, 0),
    ())

Topic._op_getPublisher = IcePy.Operation(
    "getPublisher",
    "getPublisher",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), _Ice_ObjectPrx_t, False, 0),
    ())

Topic._op_getNonReplicatedPublisher = IcePy.Operation(
    "getNonReplicatedPublisher",
    "getNonReplicatedPublisher",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), _Ice_ObjectPrx_t, False, 0),
    ())

Topic._op_subscribeAndGetPublisher = IcePy.Operation(
    "subscribeAndGetPublisher",
    "subscribeAndGetPublisher",
    OperationMode.Normal,
    None,
    (),
    (((), _IceStorm_QoS_t, False, 0), ((), _Ice_ObjectPrx_t, False, 0)),
    (),
    ((), _Ice_ObjectPrx_t, False, 0),
    (_IceStorm_AlreadySubscribed_t, _IceStorm_BadQoS_t))

Topic._op_unsubscribe = IcePy.Operation(
    "unsubscribe",
    "unsubscribe",
    OperationMode.Idempotent,
    None,
    (),
    (((), _Ice_ObjectPrx_t, False, 0),),
    (),
    None,
    ())

Topic._op_link = IcePy.Operation(
    "link",
    "link",
    OperationMode.Normal,
    None,
    (),
    (((), _IceStorm_TopicPrx_t, False, 0), ((), IcePy._t_int, False, 0)),
    (),
    None,
    (_IceStorm_LinkExists_t,))

Topic._op_unlink = IcePy.Operation(
    "unlink",
    "unlink",
    OperationMode.Normal,
    None,
    (),
    (((), _IceStorm_TopicPrx_t, False, 0),),
    (),
    None,
    (_IceStorm_NoSuchLink_t,))

Topic._op_getLinkInfoSeq = IcePy.Operation(
    "getLinkInfoSeq",
    "getLinkInfoSeq",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), _IceStorm_LinkInfoSeq_t, False, 0),
    ())

Topic._op_getSubscribers = IcePy.Operation(
    "getSubscribers",
    "getSubscribers",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    ((), _Ice_IdentitySeq_t, False, 0),
    ())

Topic._op_destroy = IcePy.Operation(
    "destroy",
    "destroy",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    None,
    ())

__all__ = ["Topic", "TopicPrx", "_IceStorm_TopicPrx_t"]
