# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Glacier2.PermissionDeniedException import _Glacier2_PermissionDeniedException_t

from Glacier2.SSLInfo import _Glacier2_SSLInfo_t

from Glacier2.SSLPermissionsVerifier_forward import _Glacier2_SSLPermissionsVerifierPrx_t

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
    from Glacier2.SSLInfo import SSLInfo
    from Ice.Current import Current
    from collections.abc import Awaitable
    from collections.abc import Sequence


class SSLPermissionsVerifierPrx(ObjectPrx):
    """
    Represents an object that checks user permissions. The Glacier2 router and other services use an
    :class:`Glacier2.SSLPermissionsVerifierPrx` proxy when the user is authenticated through an SSL certificate.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::Glacier2::SSLPermissionsVerifier``.
    """

    def authorize(self, info: SSLInfo, context: dict[str, str] | None = None) -> tuple[bool, str]:
        """
        Checks if a user is authorized to establish a session.
        
        Parameters
        ----------
        info : SSLInfo
            The SSL information.
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
        return SSLPermissionsVerifier._op_authorize.invoke(self, ((info, ), context))

    def authorizeAsync(self, info: SSLInfo, context: dict[str, str] | None = None) -> Awaitable[tuple[bool, str]]:
        """
        Checks if a user is authorized to establish a session.
        
        Parameters
        ----------
        info : SSLInfo
            The SSL information.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[tuple[bool, str]]
        
            A tuple containing:
                - bool ``true`` if access is granted, ``false`` otherwise.
                - str The reason why access was denied.
        """
        return SSLPermissionsVerifier._op_authorize.invokeAsync(self, ((info, ), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> SSLPermissionsVerifierPrx | None:
        return checkedCast(SSLPermissionsVerifierPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[SSLPermissionsVerifierPrx | None ]:
        return checkedCastAsync(SSLPermissionsVerifierPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> SSLPermissionsVerifierPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> SSLPermissionsVerifierPrx | None:
        return uncheckedCast(SSLPermissionsVerifierPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::Glacier2::SSLPermissionsVerifier"

IcePy.defineProxy("::Glacier2::SSLPermissionsVerifier", SSLPermissionsVerifierPrx)

class SSLPermissionsVerifier(Object, ABC):
    """
    Represents an object that checks user permissions. The Glacier2 router and other services use an
    :class:`Glacier2.SSLPermissionsVerifierPrx` proxy when the user is authenticated through an SSL certificate.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::Glacier2::SSLPermissionsVerifier``.
    """

    _ice_ids: Sequence[str] = ("::Glacier2::SSLPermissionsVerifier", "::Ice::Object", )
    _op_authorize: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::Glacier2::SSLPermissionsVerifier"

    @abstractmethod
    def authorize(self, info: SSLInfo, current: Current) -> tuple[bool, str] | Awaitable[tuple[bool, str]]:
        """
        Checks if a user is authorized to establish a session.
        
        Parameters
        ----------
        info : SSLInfo
            The SSL information.
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

SSLPermissionsVerifier._op_authorize = IcePy.Operation(
    "authorize",
    "authorize",
    OperationMode.Idempotent,
    None,
    (),
    (((), _Glacier2_SSLInfo_t, False, 0),),
    (((), IcePy._t_string, False, 0),),
    ((), IcePy._t_bool, False, 0),
    (_Glacier2_PermissionDeniedException_t,))

__all__ = ["SSLPermissionsVerifier", "SSLPermissionsVerifierPrx", "_Glacier2_SSLPermissionsVerifierPrx_t"]
