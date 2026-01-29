# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Glacier2.Session import Session as _m_Glacier2_Session_Session
from Glacier2.Session import SessionPrx as _m_Glacier2_Session_SessionPrx

from Ice.Identity import _Ice_Identity_t

from Ice.ObjectPrx import checkedCast
from Ice.ObjectPrx import checkedCastAsync
from Ice.ObjectPrx import uncheckedCast

from Ice.ObjectPrx_forward import _Ice_ObjectPrx_t

from Ice.OperationMode import OperationMode

from IceGrid.AllocationException import _IceGrid_AllocationException_t

from IceGrid.ObjectNotRegisteredException import _IceGrid_ObjectNotRegisteredException_t

from IceGrid.Session_forward import _IceGrid_SessionPrx_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from Ice.Identity import Identity
    from Ice.ObjectPrx import ObjectPrx
    from collections.abc import Awaitable
    from collections.abc import Sequence


class SessionPrx(_m_Glacier2_Session_SessionPrx):
    """
    Represents a session object used by IceGrid clients to allocate and release objects. Client sessions are created
    either via the :class:`IceGrid.RegistryPrx` object or via the registry client :class:`Glacier2.SessionManagerPrx` object.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::IceGrid::Session``.
    """

    def keepAlive(self, context: dict[str, str] | None = None) -> None:
        """
        Keeps the session alive.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        """
        return Session._op_keepAlive.invoke(self, ((), context))

    def keepAliveAsync(self, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Keeps the session alive.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Session._op_keepAlive.invokeAsync(self, ((), context))

    def allocateObjectById(self, id: Identity, context: dict[str, str] | None = None) -> ObjectPrx | None:
        """
        Allocates an object.
        
        Parameters
        ----------
        id : Identity
            The identity of the object to allocate.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ObjectPrx | None
            A proxy to the allocated object. This proxy is never null.
        
        Raises
        ------
        AllocationException
            Thrown when the allocation fails.
        ObjectNotRegisteredException
            Thrown when an object with the given identity is not registered with
            the registry.
        
        See Also
        --------
            :meth:`IceGrid.SessionPrx.setAllocationTimeoutAsync`
            :meth:`IceGrid.SessionPrx.releaseObjectAsync`
        """
        return Session._op_allocateObjectById.invoke(self, ((id, ), context))

    def allocateObjectByIdAsync(self, id: Identity, context: dict[str, str] | None = None) -> Awaitable[ObjectPrx | None]:
        """
        Allocates an object.
        
        Parameters
        ----------
        id : Identity
            The identity of the object to allocate.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ObjectPrx | None]
            A proxy to the allocated object. This proxy is never null.
        
        See Also
        --------
            :meth:`IceGrid.SessionPrx.setAllocationTimeoutAsync`
            :meth:`IceGrid.SessionPrx.releaseObjectAsync`
        """
        return Session._op_allocateObjectById.invokeAsync(self, ((id, ), context))

    def allocateObjectByType(self, type: str, context: dict[str, str] | None = None) -> ObjectPrx | None:
        """
        Allocates an object with the given type.
        
        Parameters
        ----------
        type : str
            The type of the object.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ObjectPrx | None
            A proxy to the allocated object. This proxy is never null.
        
        Raises
        ------
        AllocationException
            Thrown when the allocation fails.
        
        See Also
        --------
            :meth:`IceGrid.SessionPrx.setAllocationTimeoutAsync`
            :meth:`IceGrid.SessionPrx.releaseObjectAsync`
        """
        return Session._op_allocateObjectByType.invoke(self, ((type, ), context))

    def allocateObjectByTypeAsync(self, type: str, context: dict[str, str] | None = None) -> Awaitable[ObjectPrx | None]:
        """
        Allocates an object with the given type.
        
        Parameters
        ----------
        type : str
            The type of the object.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ObjectPrx | None]
            A proxy to the allocated object. This proxy is never null.
        
        See Also
        --------
            :meth:`IceGrid.SessionPrx.setAllocationTimeoutAsync`
            :meth:`IceGrid.SessionPrx.releaseObjectAsync`
        """
        return Session._op_allocateObjectByType.invokeAsync(self, ((type, ), context))

    def releaseObject(self, id: Identity, context: dict[str, str] | None = None) -> None:
        """
        Releases an object that was allocated using :meth:`IceGrid.SessionPrx.allocateObjectByIdAsync` or :meth:`IceGrid.SessionPrx.allocateObjectByTypeAsync`.
        
        Parameters
        ----------
        id : Identity
            The identity of the object to release.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        AllocationException
            Thrown when the object can't be released. This can happen when the object is not
            allocatable or is not allocated by this session.
        ObjectNotRegisteredException
            Thrown when an object with the given identity is not registered with
            the registry.
        """
        return Session._op_releaseObject.invoke(self, ((id, ), context))

    def releaseObjectAsync(self, id: Identity, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Releases an object that was allocated using :meth:`IceGrid.SessionPrx.allocateObjectByIdAsync` or :meth:`IceGrid.SessionPrx.allocateObjectByTypeAsync`.
        
        Parameters
        ----------
        id : Identity
            The identity of the object to release.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Session._op_releaseObject.invokeAsync(self, ((id, ), context))

    def setAllocationTimeout(self, timeout: int, context: dict[str, str] | None = None) -> None:
        """
        Sets the allocation timeout. When no object is immediately available for an allocation request, the
        implementation of :meth:`IceGrid.SessionPrx.allocateObjectByIdAsync` and :meth:`IceGrid.SessionPrx.allocateObjectByTypeAsync` waits for the duration of
        this ``timeout``.
        
        Parameters
        ----------
        timeout : int
            The timeout in milliseconds.
        context : dict[str, str]
            The request context for the invocation.
        """
        return Session._op_setAllocationTimeout.invoke(self, ((timeout, ), context))

    def setAllocationTimeoutAsync(self, timeout: int, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Sets the allocation timeout. When no object is immediately available for an allocation request, the
        implementation of :meth:`IceGrid.SessionPrx.allocateObjectByIdAsync` and :meth:`IceGrid.SessionPrx.allocateObjectByTypeAsync` waits for the duration of
        this ``timeout``.
        
        Parameters
        ----------
        timeout : int
            The timeout in milliseconds.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Session._op_setAllocationTimeout.invokeAsync(self, ((timeout, ), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> SessionPrx | None:
        return checkedCast(SessionPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[SessionPrx | None ]:
        return checkedCastAsync(SessionPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> SessionPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> SessionPrx | None:
        return uncheckedCast(SessionPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::Session"

IcePy.defineProxy("::IceGrid::Session", SessionPrx)

class Session(_m_Glacier2_Session_Session, ABC):
    """
    Represents a session object used by IceGrid clients to allocate and release objects. Client sessions are created
    either via the :class:`IceGrid.RegistryPrx` object or via the registry client :class:`Glacier2.SessionManagerPrx` object.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::IceGrid::Session``.
    """

    _ice_ids: Sequence[str] = ("::Glacier2::Session", "::Ice::Object", "::IceGrid::Session", )
    _op_keepAlive: IcePy.Operation
    _op_allocateObjectById: IcePy.Operation
    _op_allocateObjectByType: IcePy.Operation
    _op_releaseObject: IcePy.Operation
    _op_setAllocationTimeout: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::Session"

    @abstractmethod
    def keepAlive(self, current: Current) -> None | Awaitable[None]:
        """
        Keeps the session alive.
        
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

    @abstractmethod
    def allocateObjectById(self, id: Identity, current: Current) -> ObjectPrx | None | Awaitable[ObjectPrx | None]:
        """
        Allocates an object.
        
        Parameters
        ----------
        id : Identity
            The identity of the object to allocate.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ObjectPrx | None | Awaitable[ObjectPrx | None]
            A proxy to the allocated object. This proxy is never null.
        
        Raises
        ------
        AllocationException
            Thrown when the allocation fails.
        ObjectNotRegisteredException
            Thrown when an object with the given identity is not registered with
            the registry.
        
        See Also
        --------
            :meth:`IceGrid.SessionPrx.setAllocationTimeoutAsync`
            :meth:`IceGrid.SessionPrx.releaseObjectAsync`
        """
        pass

    @abstractmethod
    def allocateObjectByType(self, type: str, current: Current) -> ObjectPrx | None | Awaitable[ObjectPrx | None]:
        """
        Allocates an object with the given type.
        
        Parameters
        ----------
        type : str
            The type of the object.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ObjectPrx | None | Awaitable[ObjectPrx | None]
            A proxy to the allocated object. This proxy is never null.
        
        Raises
        ------
        AllocationException
            Thrown when the allocation fails.
        
        See Also
        --------
            :meth:`IceGrid.SessionPrx.setAllocationTimeoutAsync`
            :meth:`IceGrid.SessionPrx.releaseObjectAsync`
        """
        pass

    @abstractmethod
    def releaseObject(self, id: Identity, current: Current) -> None | Awaitable[None]:
        """
        Releases an object that was allocated using :meth:`IceGrid.SessionPrx.allocateObjectByIdAsync` or :meth:`IceGrid.SessionPrx.allocateObjectByTypeAsync`.
        
        Parameters
        ----------
        id : Identity
            The identity of the object to release.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        AllocationException
            Thrown when the object can't be released. This can happen when the object is not
            allocatable or is not allocated by this session.
        ObjectNotRegisteredException
            Thrown when an object with the given identity is not registered with
            the registry.
        """
        pass

    @abstractmethod
    def setAllocationTimeout(self, timeout: int, current: Current) -> None | Awaitable[None]:
        """
        Sets the allocation timeout. When no object is immediately available for an allocation request, the
        implementation of :meth:`IceGrid.SessionPrx.allocateObjectByIdAsync` and :meth:`IceGrid.SessionPrx.allocateObjectByTypeAsync` waits for the duration of
        this ``timeout``.
        
        Parameters
        ----------
        timeout : int
            The timeout in milliseconds.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

Session._op_keepAlive = IcePy.Operation(
    "keepAlive",
    "keepAlive",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    None,
    ())
Session._op_keepAlive.deprecate("As of Ice 3.8, there is no need to call this operation, and its implementation does nothing.")

Session._op_allocateObjectById = IcePy.Operation(
    "allocateObjectById",
    "allocateObjectById",
    OperationMode.Normal,
    None,
    (),
    (((), _Ice_Identity_t, False, 0),),
    (),
    ((), _Ice_ObjectPrx_t, False, 0),
    (_IceGrid_ObjectNotRegisteredException_t, _IceGrid_AllocationException_t))

Session._op_allocateObjectByType = IcePy.Operation(
    "allocateObjectByType",
    "allocateObjectByType",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _Ice_ObjectPrx_t, False, 0),
    (_IceGrid_AllocationException_t,))

Session._op_releaseObject = IcePy.Operation(
    "releaseObject",
    "releaseObject",
    OperationMode.Normal,
    None,
    (),
    (((), _Ice_Identity_t, False, 0),),
    (),
    None,
    (_IceGrid_ObjectNotRegisteredException_t, _IceGrid_AllocationException_t))

Session._op_setAllocationTimeout = IcePy.Operation(
    "setAllocationTimeout",
    "setAllocationTimeout",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_int, False, 0),),
    (),
    None,
    ())

__all__ = ["Session", "SessionPrx", "_IceGrid_SessionPrx_t"]
