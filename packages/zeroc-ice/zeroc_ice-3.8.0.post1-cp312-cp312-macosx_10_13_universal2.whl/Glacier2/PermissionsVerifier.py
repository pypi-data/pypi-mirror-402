# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Glacier2.PermissionDeniedException import _Glacier2_PermissionDeniedException_t

from Glacier2.PermissionsVerifier_forward import _Glacier2_PermissionsVerifierPrx_t

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
    from collections.abc import Awaitable
    from collections.abc import Sequence


class PermissionsVerifierPrx(ObjectPrx):
    """
    Represents an object that checks user permissions. The Glacier2 router and other services use a
    :class:`Glacier2.PermissionsVerifierPrx` proxy when the user is authenticated using a user ID and password.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::Glacier2::PermissionsVerifier``.
    """

    def checkPermissions(self, userId: str, password: str, context: dict[str, str] | None = None) -> tuple[bool, str]:
        """
        Checks if a user is authorized to establish a session.
        
        Parameters
        ----------
        userId : str
            The user ID.
        password : str
            The user's password.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        tuple[bool, str]
        
            A tuple containing:
                - bool ``true`` if access is granted, ``false`` otherwise.
                - str The reason why access was denied.
        
        Raises
        ------
        PermissionDeniedException
            Thrown when the user's access is denied. This exception can be thrown
            instead of returning ``false`` with a reason set in the reason out parameter.
        """
        return PermissionsVerifier._op_checkPermissions.invoke(self, ((userId, password), context))

    def checkPermissionsAsync(self, userId: str, password: str, context: dict[str, str] | None = None) -> Awaitable[tuple[bool, str]]:
        """
        Checks if a user is authorized to establish a session.
        
        Parameters
        ----------
        userId : str
            The user ID.
        password : str
            The user's password.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[tuple[bool, str]]
        
            A tuple containing:
                - bool ``true`` if access is granted, ``false`` otherwise.
                - str The reason why access was denied.
        """
        return PermissionsVerifier._op_checkPermissions.invokeAsync(self, ((userId, password), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> PermissionsVerifierPrx | None:
        return checkedCast(PermissionsVerifierPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[PermissionsVerifierPrx | None ]:
        return checkedCastAsync(PermissionsVerifierPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> PermissionsVerifierPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> PermissionsVerifierPrx | None:
        return uncheckedCast(PermissionsVerifierPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::Glacier2::PermissionsVerifier"

IcePy.defineProxy("::Glacier2::PermissionsVerifier", PermissionsVerifierPrx)

class PermissionsVerifier(Object, ABC):
    """
    Represents an object that checks user permissions. The Glacier2 router and other services use a
    :class:`Glacier2.PermissionsVerifierPrx` proxy when the user is authenticated using a user ID and password.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::Glacier2::PermissionsVerifier``.
    """

    _ice_ids: Sequence[str] = ("::Glacier2::PermissionsVerifier", "::Ice::Object", )
    _op_checkPermissions: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::Glacier2::PermissionsVerifier"

    @abstractmethod
    def checkPermissions(self, userId: str, password: str, current: Current) -> tuple[bool, str] | Awaitable[tuple[bool, str]]:
        """
        Checks if a user is authorized to establish a session.
        
        Parameters
        ----------
        userId : str
            The user ID.
        password : str
            The user's password.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        tuple[bool, str] | Awaitable[tuple[bool, str]]
        
            A tuple containing:
                - bool ``true`` if access is granted, ``false`` otherwise.
                - str The reason why access was denied.
        
        Raises
        ------
        PermissionDeniedException
            Thrown when the user's access is denied. This exception can be thrown
            instead of returning ``false`` with a reason set in the reason out parameter.
        """
        pass

PermissionsVerifier._op_checkPermissions = IcePy.Operation(
    "checkPermissions",
    "checkPermissions",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0)),
    (((), IcePy._t_string, False, 0),),
    ((), IcePy._t_bool, False, 0),
    (_Glacier2_PermissionDeniedException_t,))

__all__ = ["PermissionsVerifier", "PermissionsVerifierPrx", "_Glacier2_PermissionsVerifierPrx_t"]
