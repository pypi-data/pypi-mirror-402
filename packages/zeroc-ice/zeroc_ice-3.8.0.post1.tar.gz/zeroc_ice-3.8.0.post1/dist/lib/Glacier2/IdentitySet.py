# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Glacier2.IdentitySet_forward import _Glacier2_IdentitySetPrx_t

from Ice.IdentitySeq import _Ice_IdentitySeq_t

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
    from Ice.Current import Current
    from Ice.Identity import Identity
    from collections.abc import Awaitable
    from collections.abc import Sequence


class IdentitySetPrx(ObjectPrx):
    """
    Manages a set of object identity constraints on a :class:`Glacier2.SessionPrx`.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::Glacier2::IdentitySet``.
    
    See Also
    --------
        :class:`Glacier2.SessionControlPrx`
    """

    def add(self, additions: Sequence[Identity], context: dict[str, str] | None = None) -> None:
        """
        Adds a sequence of Ice identities to this set of constraints. Order is not preserved and duplicates are
        implicitly removed.
        
        Parameters
        ----------
        additions : Sequence[Identity]
            The sequence of Ice identities to add.
        context : dict[str, str]
            The request context for the invocation.
        """
        return IdentitySet._op_add.invoke(self, ((additions, ), context))

    def addAsync(self, additions: Sequence[Identity], context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Adds a sequence of Ice identities to this set of constraints. Order is not preserved and duplicates are
        implicitly removed.
        
        Parameters
        ----------
        additions : Sequence[Identity]
            The sequence of Ice identities to add.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return IdentitySet._op_add.invokeAsync(self, ((additions, ), context))

    def remove(self, deletions: Sequence[Identity], context: dict[str, str] | None = None) -> None:
        """
        Removes a sequence of identities from this set of constraints. No errors are returned if an entry is not
        found.
        
        Parameters
        ----------
        deletions : Sequence[Identity]
            The sequence of Ice identities to remove.
        context : dict[str, str]
            The request context for the invocation.
        """
        return IdentitySet._op_remove.invoke(self, ((deletions, ), context))

    def removeAsync(self, deletions: Sequence[Identity], context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Removes a sequence of identities from this set of constraints. No errors are returned if an entry is not
        found.
        
        Parameters
        ----------
        deletions : Sequence[Identity]
            The sequence of Ice identities to remove.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return IdentitySet._op_remove.invokeAsync(self, ((deletions, ), context))

    def get(self, context: dict[str, str] | None = None) -> list[Identity]:
        """
        Gets a sequence of identities describing the constraints in this set.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        list[Identity]
            The sequence of Ice identities for this set.
        """
        return IdentitySet._op_get.invoke(self, ((), context))

    def getAsync(self, context: dict[str, str] | None = None) -> Awaitable[list[Identity]]:
        """
        Gets a sequence of identities describing the constraints in this set.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[list[Identity]]
            The sequence of Ice identities for this set.
        """
        return IdentitySet._op_get.invokeAsync(self, ((), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> IdentitySetPrx | None:
        return checkedCast(IdentitySetPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[IdentitySetPrx | None ]:
        return checkedCastAsync(IdentitySetPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> IdentitySetPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> IdentitySetPrx | None:
        return uncheckedCast(IdentitySetPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::Glacier2::IdentitySet"

IcePy.defineProxy("::Glacier2::IdentitySet", IdentitySetPrx)

class IdentitySet(Object, ABC):
    """
    Manages a set of object identity constraints on a :class:`Glacier2.SessionPrx`.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::Glacier2::IdentitySet``.
    
    See Also
    --------
        :class:`Glacier2.SessionControlPrx`
    """

    _ice_ids: Sequence[str] = ("::Glacier2::IdentitySet", "::Ice::Object", )
    _op_add: IcePy.Operation
    _op_remove: IcePy.Operation
    _op_get: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::Glacier2::IdentitySet"

    @abstractmethod
    def add(self, additions: list[Identity], current: Current) -> None | Awaitable[None]:
        """
        Adds a sequence of Ice identities to this set of constraints. Order is not preserved and duplicates are
        implicitly removed.
        
        Parameters
        ----------
        additions : list[Identity]
            The sequence of Ice identities to add.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def remove(self, deletions: list[Identity], current: Current) -> None | Awaitable[None]:
        """
        Removes a sequence of identities from this set of constraints. No errors are returned if an entry is not
        found.
        
        Parameters
        ----------
        deletions : list[Identity]
            The sequence of Ice identities to remove.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def get(self, current: Current) -> Sequence[Identity] | Awaitable[Sequence[Identity]]:
        """
        Gets a sequence of identities describing the constraints in this set.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        Sequence[Identity] | Awaitable[Sequence[Identity]]
            The sequence of Ice identities for this set.
        """
        pass

IdentitySet._op_add = IcePy.Operation(
    "add",
    "add",
    OperationMode.Idempotent,
    None,
    (),
    (((), _Ice_IdentitySeq_t, False, 0),),
    (),
    None,
    ())

IdentitySet._op_remove = IcePy.Operation(
    "remove",
    "remove",
    OperationMode.Idempotent,
    None,
    (),
    (((), _Ice_IdentitySeq_t, False, 0),),
    (),
    None,
    ())

IdentitySet._op_get = IcePy.Operation(
    "get",
    "get",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), _Ice_IdentitySeq_t, False, 0),
    ())

__all__ = ["IdentitySet", "IdentitySetPrx", "_Glacier2_IdentitySetPrx_t"]
