# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Glacier2.IdentitySet_forward import _Glacier2_IdentitySetPrx_t

from Glacier2.SessionControl_forward import _Glacier2_SessionControlPrx_t

from Glacier2.StringSet_forward import _Glacier2_StringSetPrx_t

from Ice.Object import Object

from Ice.ObjectPrx import ObjectPrx
from Ice.ObjectPrx import checkedCast
from Ice.ObjectPrx import checkedCastAsync
from Ice.ObjectPrx import uncheckedCast

from Ice.OperationMode import OperationMode

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Glacier2.IdentitySet import IdentitySetPrx
    from Glacier2.StringSet import StringSetPrx
    from Ice.Current import Current
    from collections.abc import Awaitable
    from collections.abc import Sequence


class SessionControlPrx(ObjectPrx):
    """
    Represents a router-provided object that allows an application-provided session manager to configure the
    routing constraints for a session.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::Glacier2::SessionControl``.
    
    See Also
    --------
        :class:`Glacier2.SessionManagerPrx`
    """

    def categories(self, context: dict[str, str] | None = None) -> StringSetPrx | None:
        """
        Gets a proxy to the object that manages the allowable categories for object identities for this session.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        StringSetPrx | None
            A proxy to a :class:`Glacier2.StringSetPrx` object. This proxy is never null.
        """
        return SessionControl._op_categories.invoke(self, ((), context))

    def categoriesAsync(self, context: dict[str, str] | None = None) -> Awaitable[StringSetPrx | None]:
        """
        Gets a proxy to the object that manages the allowable categories for object identities for this session.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[StringSetPrx | None]
            A proxy to a :class:`Glacier2.StringSetPrx` object. This proxy is never null.
        """
        return SessionControl._op_categories.invokeAsync(self, ((), context))

    def adapterIds(self, context: dict[str, str] | None = None) -> StringSetPrx | None:
        """
        Gets a proxy to the object that manages the allowable adapter identities for objects for this session.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        StringSetPrx | None
            A proxy to a :class:`Glacier2.StringSetPrx` object. This proxy is never null.
        """
        return SessionControl._op_adapterIds.invoke(self, ((), context))

    def adapterIdsAsync(self, context: dict[str, str] | None = None) -> Awaitable[StringSetPrx | None]:
        """
        Gets a proxy to the object that manages the allowable adapter identities for objects for this session.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[StringSetPrx | None]
            A proxy to a :class:`Glacier2.StringSetPrx` object. This proxy is never null.
        """
        return SessionControl._op_adapterIds.invokeAsync(self, ((), context))

    def identities(self, context: dict[str, str] | None = None) -> IdentitySetPrx | None:
        """
        Gets a proxy to the object that manages the allowable object identities for this session.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        IdentitySetPrx | None
            A proxy to an :class:`Glacier2.IdentitySetPrx` object. This proxy is never null.
        """
        return SessionControl._op_identities.invoke(self, ((), context))

    def identitiesAsync(self, context: dict[str, str] | None = None) -> Awaitable[IdentitySetPrx | None]:
        """
        Gets a proxy to the object that manages the allowable object identities for this session.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[IdentitySetPrx | None]
            A proxy to an :class:`Glacier2.IdentitySetPrx` object. This proxy is never null.
        """
        return SessionControl._op_identities.invokeAsync(self, ((), context))

    def getSessionTimeout(self, context: dict[str, str] | None = None) -> int:
        """
        Gets the session timeout.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        int
            The timeout.
        """
        return SessionControl._op_getSessionTimeout.invoke(self, ((), context))

    def getSessionTimeoutAsync(self, context: dict[str, str] | None = None) -> Awaitable[int]:
        """
        Gets the session timeout.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[int]
            The timeout.
        """
        return SessionControl._op_getSessionTimeout.invokeAsync(self, ((), context))

    def destroy(self, context: dict[str, str] | None = None) -> None:
        """
        Destroys the associated session.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        """
        return SessionControl._op_destroy.invoke(self, ((), context))

    def destroyAsync(self, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Destroys the associated session.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return SessionControl._op_destroy.invokeAsync(self, ((), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> SessionControlPrx | None:
        return checkedCast(SessionControlPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[SessionControlPrx | None ]:
        return checkedCastAsync(SessionControlPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> SessionControlPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> SessionControlPrx | None:
        return uncheckedCast(SessionControlPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::Glacier2::SessionControl"

IcePy.defineProxy("::Glacier2::SessionControl", SessionControlPrx)

class SessionControl(Object, ABC):
    """
    Represents a router-provided object that allows an application-provided session manager to configure the
    routing constraints for a session.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::Glacier2::SessionControl``.
    
    See Also
    --------
        :class:`Glacier2.SessionManagerPrx`
    """

    _ice_ids: Sequence[str] = ("::Glacier2::SessionControl", "::Ice::Object", )
    _op_categories: IcePy.Operation
    _op_adapterIds: IcePy.Operation
    _op_identities: IcePy.Operation
    _op_getSessionTimeout: IcePy.Operation
    _op_destroy: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::Glacier2::SessionControl"

    @abstractmethod
    def categories(self, current: Current) -> StringSetPrx | None | Awaitable[StringSetPrx | None]:
        """
        Gets a proxy to the object that manages the allowable categories for object identities for this session.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        StringSetPrx | None | Awaitable[StringSetPrx | None]
            A proxy to a :class:`Glacier2.StringSetPrx` object. This proxy is never null.
        """
        pass

    @abstractmethod
    def adapterIds(self, current: Current) -> StringSetPrx | None | Awaitable[StringSetPrx | None]:
        """
        Gets a proxy to the object that manages the allowable adapter identities for objects for this session.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        StringSetPrx | None | Awaitable[StringSetPrx | None]
            A proxy to a :class:`Glacier2.StringSetPrx` object. This proxy is never null.
        """
        pass

    @abstractmethod
    def identities(self, current: Current) -> IdentitySetPrx | None | Awaitable[IdentitySetPrx | None]:
        """
        Gets a proxy to the object that manages the allowable object identities for this session.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        IdentitySetPrx | None | Awaitable[IdentitySetPrx | None]
            A proxy to an :class:`Glacier2.IdentitySetPrx` object. This proxy is never null.
        """
        pass

    @abstractmethod
    def getSessionTimeout(self, current: Current) -> int | Awaitable[int]:
        """
        Gets the session timeout.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        int | Awaitable[int]
            The timeout.
        """
        pass

    @abstractmethod
    def destroy(self, current: Current) -> None | Awaitable[None]:
        """
        Destroys the associated session.
        
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

SessionControl._op_categories = IcePy.Operation(
    "categories",
    "categories",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    ((), _Glacier2_StringSetPrx_t, False, 0),
    ())

SessionControl._op_adapterIds = IcePy.Operation(
    "adapterIds",
    "adapterIds",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    ((), _Glacier2_StringSetPrx_t, False, 0),
    ())

SessionControl._op_identities = IcePy.Operation(
    "identities",
    "identities",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    ((), _Glacier2_IdentitySetPrx_t, False, 0),
    ())

SessionControl._op_getSessionTimeout = IcePy.Operation(
    "getSessionTimeout",
    "getSessionTimeout",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), IcePy._t_int, False, 0),
    ())

SessionControl._op_destroy = IcePy.Operation(
    "destroy",
    "destroy",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    None,
    ())

__all__ = ["SessionControl", "SessionControlPrx", "_Glacier2_SessionControlPrx_t"]
