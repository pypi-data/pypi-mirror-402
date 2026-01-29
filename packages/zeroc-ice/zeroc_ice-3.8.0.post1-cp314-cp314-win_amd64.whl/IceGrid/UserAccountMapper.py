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

from IceGrid.UserAccountMapper_forward import _IceGrid_UserAccountMapperPrx_t

from IceGrid.UserAccountNotFoundException import _IceGrid_UserAccountNotFoundException_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from collections.abc import Awaitable
    from collections.abc import Sequence


class UserAccountMapperPrx(ObjectPrx):
    """
    Maps user strings in server descriptors to actual user account names. You can configure the user account mapper
    of an IceGrid node with the property ``IceGrid.Node.UserAccountMapper``.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::IceGrid::UserAccountMapper``.
    """

    def getUserAccount(self, user: str, context: dict[str, str] | None = None) -> str:
        """
        Gets the name of the user account for the given user. This is used by IceGrid nodes to figure out the user
        account to use to run servers.
        
        Parameters
        ----------
        user : str
            The value of the server descriptor's ``user`` attribute. When this attribute is not defined, and
            the server's activation mode is ``session``, the default value for ``user`` is the session identifier.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        str
            The user account name.
        
        Raises
        ------
        UserAccountNotFoundException
            Thrown when no user account is found for the given user.
        """
        return UserAccountMapper._op_getUserAccount.invoke(self, ((user, ), context))

    def getUserAccountAsync(self, user: str, context: dict[str, str] | None = None) -> Awaitable[str]:
        """
        Gets the name of the user account for the given user. This is used by IceGrid nodes to figure out the user
        account to use to run servers.
        
        Parameters
        ----------
        user : str
            The value of the server descriptor's ``user`` attribute. When this attribute is not defined, and
            the server's activation mode is ``session``, the default value for ``user`` is the session identifier.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[str]
            The user account name.
        """
        return UserAccountMapper._op_getUserAccount.invokeAsync(self, ((user, ), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> UserAccountMapperPrx | None:
        return checkedCast(UserAccountMapperPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[UserAccountMapperPrx | None ]:
        return checkedCastAsync(UserAccountMapperPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> UserAccountMapperPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> UserAccountMapperPrx | None:
        return uncheckedCast(UserAccountMapperPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::UserAccountMapper"

IcePy.defineProxy("::IceGrid::UserAccountMapper", UserAccountMapperPrx)

class UserAccountMapper(Object, ABC):
    """
    Maps user strings in server descriptors to actual user account names. You can configure the user account mapper
    of an IceGrid node with the property ``IceGrid.Node.UserAccountMapper``.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::IceGrid::UserAccountMapper``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::IceGrid::UserAccountMapper", )
    _op_getUserAccount: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::UserAccountMapper"

    @abstractmethod
    def getUserAccount(self, user: str, current: Current) -> str | Awaitable[str]:
        """
        Gets the name of the user account for the given user. This is used by IceGrid nodes to figure out the user
        account to use to run servers.
        
        Parameters
        ----------
        user : str
            The value of the server descriptor's ``user`` attribute. When this attribute is not defined, and
            the server's activation mode is ``session``, the default value for ``user`` is the session identifier.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        str | Awaitable[str]
            The user account name.
        
        Raises
        ------
        UserAccountNotFoundException
            Thrown when no user account is found for the given user.
        """
        pass

UserAccountMapper._op_getUserAccount = IcePy.Operation(
    "getUserAccount",
    "getUserAccount",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), IcePy._t_string, False, 0),
    (_IceGrid_UserAccountNotFoundException_t,))

__all__ = ["UserAccountMapper", "UserAccountMapperPrx", "_IceGrid_UserAccountMapperPrx_t"]
