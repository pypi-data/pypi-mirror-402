# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Glacier2.StringSet_forward import _Glacier2_StringSetPrx_t

from Ice.Object import Object

from Ice.ObjectPrx import ObjectPrx
from Ice.ObjectPrx import checkedCast
from Ice.ObjectPrx import checkedCastAsync
from Ice.ObjectPrx import uncheckedCast

from Ice.OperationMode import OperationMode

from Ice.StringSeq import _Ice_StringSeq_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from collections.abc import Awaitable
    from collections.abc import Sequence


class StringSetPrx(ObjectPrx):
    """
    Manages a set of constraints on a :class:`Glacier2.SessionPrx`.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::Glacier2::StringSet``.
    
    See Also
    --------
        :class:`Glacier2.SessionControlPrx`
    """

    def add(self, additions: Sequence[str], context: dict[str, str] | None = None) -> None:
        """
        Adds a sequence of strings to this set of constraints. Order is not preserved and duplicates are implicitly
        removed.
        
        Parameters
        ----------
        additions : Sequence[str]
            The sequence of strings to add.
        context : dict[str, str]
            The request context for the invocation.
        """
        return StringSet._op_add.invoke(self, ((additions, ), context))

    def addAsync(self, additions: Sequence[str], context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Adds a sequence of strings to this set of constraints. Order is not preserved and duplicates are implicitly
        removed.
        
        Parameters
        ----------
        additions : Sequence[str]
            The sequence of strings to add.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return StringSet._op_add.invokeAsync(self, ((additions, ), context))

    def remove(self, deletions: Sequence[str], context: dict[str, str] | None = None) -> None:
        """
        Removes a sequence of strings from this set of constraints. No errors are returned if an entry is not found.
        
        Parameters
        ----------
        deletions : Sequence[str]
            The sequence of strings to remove.
        context : dict[str, str]
            The request context for the invocation.
        """
        return StringSet._op_remove.invoke(self, ((deletions, ), context))

    def removeAsync(self, deletions: Sequence[str], context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Removes a sequence of strings from this set of constraints. No errors are returned if an entry is not found.
        
        Parameters
        ----------
        deletions : Sequence[str]
            The sequence of strings to remove.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return StringSet._op_remove.invokeAsync(self, ((deletions, ), context))

    def get(self, context: dict[str, str] | None = None) -> list[str]:
        """
        Gets a sequence of strings describing the constraints in this set.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        list[str]
            The sequence of strings for this set.
        """
        return StringSet._op_get.invoke(self, ((), context))

    def getAsync(self, context: dict[str, str] | None = None) -> Awaitable[list[str]]:
        """
        Gets a sequence of strings describing the constraints in this set.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[list[str]]
            The sequence of strings for this set.
        """
        return StringSet._op_get.invokeAsync(self, ((), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> StringSetPrx | None:
        return checkedCast(StringSetPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[StringSetPrx | None ]:
        return checkedCastAsync(StringSetPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> StringSetPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> StringSetPrx | None:
        return uncheckedCast(StringSetPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::Glacier2::StringSet"

IcePy.defineProxy("::Glacier2::StringSet", StringSetPrx)

class StringSet(Object, ABC):
    """
    Manages a set of constraints on a :class:`Glacier2.SessionPrx`.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::Glacier2::StringSet``.
    
    See Also
    --------
        :class:`Glacier2.SessionControlPrx`
    """

    _ice_ids: Sequence[str] = ("::Glacier2::StringSet", "::Ice::Object", )
    _op_add: IcePy.Operation
    _op_remove: IcePy.Operation
    _op_get: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::Glacier2::StringSet"

    @abstractmethod
    def add(self, additions: list[str], current: Current) -> None | Awaitable[None]:
        """
        Adds a sequence of strings to this set of constraints. Order is not preserved and duplicates are implicitly
        removed.
        
        Parameters
        ----------
        additions : list[str]
            The sequence of strings to add.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def remove(self, deletions: list[str], current: Current) -> None | Awaitable[None]:
        """
        Removes a sequence of strings from this set of constraints. No errors are returned if an entry is not found.
        
        Parameters
        ----------
        deletions : list[str]
            The sequence of strings to remove.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def get(self, current: Current) -> Sequence[str] | Awaitable[Sequence[str]]:
        """
        Gets a sequence of strings describing the constraints in this set.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        Sequence[str] | Awaitable[Sequence[str]]
            The sequence of strings for this set.
        """
        pass

StringSet._op_add = IcePy.Operation(
    "add",
    "add",
    OperationMode.Idempotent,
    None,
    (),
    (((), _Ice_StringSeq_t, False, 0),),
    (),
    None,
    ())

StringSet._op_remove = IcePy.Operation(
    "remove",
    "remove",
    OperationMode.Idempotent,
    None,
    (),
    (((), _Ice_StringSeq_t, False, 0),),
    (),
    None,
    ())

StringSet._op_get = IcePy.Operation(
    "get",
    "get",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), _Ice_StringSeq_t, False, 0),
    ())

__all__ = ["StringSet", "StringSetPrx", "_Glacier2_StringSetPrx_t"]
