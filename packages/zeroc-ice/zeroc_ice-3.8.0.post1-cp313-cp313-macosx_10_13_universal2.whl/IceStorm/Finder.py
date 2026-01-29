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

from IceStorm.Finder_forward import _IceStorm_FinderPrx_t

from IceStorm.TopicManager_forward import _IceStorm_TopicManagerPrx_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from IceStorm.TopicManager import TopicManagerPrx
    from collections.abc import Awaitable
    from collections.abc import Sequence


class FinderPrx(ObjectPrx):
    """
    Provides access to a :class:`IceStorm.TopicManagerPrx` object via a fixed identity.
    An IceStorm Finder is always registered with identity ``IceStorm/Finder``. This allows clients to obtain the
    associated TopicManager proxy with just the endpoint information of the object. For example, you can use the
    Finder proxy ``IceStorm/Finder:tcp -h somehost -p 4061`` to get the TopicManager proxy
    ``MyIceStorm/TopicManager:tcp -h somehost -p 4061``.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::IceStorm::Finder``.
    """

    def getTopicManager(self, context: dict[str, str] | None = None) -> TopicManagerPrx | None:
        """
        Gets a proxy to the associated :class:`IceStorm.TopicManagerPrx`. The proxy might point to several replicas.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        TopicManagerPrx | None
            The topic manager proxy. This proxy is never null.
        """
        return Finder._op_getTopicManager.invoke(self, ((), context))

    def getTopicManagerAsync(self, context: dict[str, str] | None = None) -> Awaitable[TopicManagerPrx | None]:
        """
        Gets a proxy to the associated :class:`IceStorm.TopicManagerPrx`. The proxy might point to several replicas.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[TopicManagerPrx | None]
            The topic manager proxy. This proxy is never null.
        """
        return Finder._op_getTopicManager.invokeAsync(self, ((), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> FinderPrx | None:
        return checkedCast(FinderPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[FinderPrx | None ]:
        return checkedCastAsync(FinderPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> FinderPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> FinderPrx | None:
        return uncheckedCast(FinderPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceStorm::Finder"

IcePy.defineProxy("::IceStorm::Finder", FinderPrx)

class Finder(Object, ABC):
    """
    Provides access to a :class:`IceStorm.TopicManagerPrx` object via a fixed identity.
    An IceStorm Finder is always registered with identity ``IceStorm/Finder``. This allows clients to obtain the
    associated TopicManager proxy with just the endpoint information of the object. For example, you can use the
    Finder proxy ``IceStorm/Finder:tcp -h somehost -p 4061`` to get the TopicManager proxy
    ``MyIceStorm/TopicManager:tcp -h somehost -p 4061``.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::IceStorm::Finder``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::IceStorm::Finder", )
    _op_getTopicManager: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceStorm::Finder"

    @abstractmethod
    def getTopicManager(self, current: Current) -> TopicManagerPrx | None | Awaitable[TopicManagerPrx | None]:
        """
        Gets a proxy to the associated :class:`IceStorm.TopicManagerPrx`. The proxy might point to several replicas.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        TopicManagerPrx | None | Awaitable[TopicManagerPrx | None]
            The topic manager proxy. This proxy is never null.
        """
        pass

Finder._op_getTopicManager = IcePy.Operation(
    "getTopicManager",
    "getTopicManager",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    ((), _IceStorm_TopicManagerPrx_t, False, 0),
    ())

__all__ = ["Finder", "FinderPrx", "_IceStorm_FinderPrx_t"]
