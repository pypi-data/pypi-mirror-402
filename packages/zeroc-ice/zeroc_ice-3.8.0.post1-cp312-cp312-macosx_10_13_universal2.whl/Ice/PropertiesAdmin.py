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

from Ice.PropertiesAdmin_forward import _Ice_PropertiesAdminPrx_t

from Ice.PropertyDict import _Ice_PropertyDict_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from collections.abc import Awaitable
    from collections.abc import Mapping
    from collections.abc import Sequence


class PropertiesAdminPrx(ObjectPrx):
    """
    Provides remote access to the properties of a communicator.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::Ice::PropertiesAdmin``.
    """

    def getProperty(self, key: str, context: dict[str, str] | None = None) -> str:
        """
        Gets a property by key.
        
        Parameters
        ----------
        key : str
            The property key.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        str
            The property value. This value is empty if the property is not set.
        """
        return PropertiesAdmin._op_getProperty.invoke(self, ((key, ), context))

    def getPropertyAsync(self, key: str, context: dict[str, str] | None = None) -> Awaitable[str]:
        """
        Gets a property by key.
        
        Parameters
        ----------
        key : str
            The property key.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[str]
            The property value. This value is empty if the property is not set.
        """
        return PropertiesAdmin._op_getProperty.invokeAsync(self, ((key, ), context))

    def getPropertiesForPrefix(self, prefix: str, context: dict[str, str] | None = None) -> dict[str, str]:
        """
        Gets all properties whose keys begin with ``prefix``. If ``prefix`` is the empty string then all properties
        are returned.
        
        Parameters
        ----------
        prefix : str
            The prefix to search for. May be empty.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        dict[str, str]
            The matching property set.
        """
        return PropertiesAdmin._op_getPropertiesForPrefix.invoke(self, ((prefix, ), context))

    def getPropertiesForPrefixAsync(self, prefix: str, context: dict[str, str] | None = None) -> Awaitable[dict[str, str]]:
        """
        Gets all properties whose keys begin with ``prefix``. If ``prefix`` is the empty string then all properties
        are returned.
        
        Parameters
        ----------
        prefix : str
            The prefix to search for. May be empty.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[dict[str, str]]
            The matching property set.
        """
        return PropertiesAdmin._op_getPropertiesForPrefix.invokeAsync(self, ((prefix, ), context))

    def setProperties(self, newProperties: Mapping[str, str], context: dict[str, str] | None = None) -> None:
        """
        Updates the communicator's properties with the given property set. If an entry in ``newProperties`` matches
        the name of an existing property, that property's value is replaced with the new value. If the new value is
        the empty string, the property is removed. Existing properties that are not modified or removed by the
        entries in ``newProperties`` are not affected by this update.
        
        Parameters
        ----------
        newProperties : Mapping[str, str]
            Properties to add, change, or remove.
        context : dict[str, str]
            The request context for the invocation.
        """
        return PropertiesAdmin._op_setProperties.invoke(self, ((newProperties, ), context))

    def setPropertiesAsync(self, newProperties: Mapping[str, str], context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Updates the communicator's properties with the given property set. If an entry in ``newProperties`` matches
        the name of an existing property, that property's value is replaced with the new value. If the new value is
        the empty string, the property is removed. Existing properties that are not modified or removed by the
        entries in ``newProperties`` are not affected by this update.
        
        Parameters
        ----------
        newProperties : Mapping[str, str]
            Properties to add, change, or remove.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return PropertiesAdmin._op_setProperties.invokeAsync(self, ((newProperties, ), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> PropertiesAdminPrx | None:
        return checkedCast(PropertiesAdminPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[PropertiesAdminPrx | None ]:
        return checkedCastAsync(PropertiesAdminPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> PropertiesAdminPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> PropertiesAdminPrx | None:
        return uncheckedCast(PropertiesAdminPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::Ice::PropertiesAdmin"

IcePy.defineProxy("::Ice::PropertiesAdmin", PropertiesAdminPrx)

class PropertiesAdmin(Object, ABC):
    """
    Provides remote access to the properties of a communicator.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::Ice::PropertiesAdmin``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::Ice::PropertiesAdmin", )
    _op_getProperty: IcePy.Operation
    _op_getPropertiesForPrefix: IcePy.Operation
    _op_setProperties: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::Ice::PropertiesAdmin"

    @abstractmethod
    def getProperty(self, key: str, current: Current) -> str | Awaitable[str]:
        """
        Gets a property by key.
        
        Parameters
        ----------
        key : str
            The property key.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        str | Awaitable[str]
            The property value. This value is empty if the property is not set.
        """
        pass

    @abstractmethod
    def getPropertiesForPrefix(self, prefix: str, current: Current) -> Mapping[str, str] | Awaitable[Mapping[str, str]]:
        """
        Gets all properties whose keys begin with ``prefix``. If ``prefix`` is the empty string then all properties
        are returned.
        
        Parameters
        ----------
        prefix : str
            The prefix to search for. May be empty.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        Mapping[str, str] | Awaitable[Mapping[str, str]]
            The matching property set.
        """
        pass

    @abstractmethod
    def setProperties(self, newProperties: dict[str, str], current: Current) -> None | Awaitable[None]:
        """
        Updates the communicator's properties with the given property set. If an entry in ``newProperties`` matches
        the name of an existing property, that property's value is replaced with the new value. If the new value is
        the empty string, the property is removed. Existing properties that are not modified or removed by the
        entries in ``newProperties`` are not affected by this update.
        
        Parameters
        ----------
        newProperties : dict[str, str]
            Properties to add, change, or remove.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

PropertiesAdmin._op_getProperty = IcePy.Operation(
    "getProperty",
    "getProperty",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), IcePy._t_string, False, 0),
    ())

PropertiesAdmin._op_getPropertiesForPrefix = IcePy.Operation(
    "getPropertiesForPrefix",
    "getPropertiesForPrefix",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _Ice_PropertyDict_t, False, 0),
    ())

PropertiesAdmin._op_setProperties = IcePy.Operation(
    "setProperties",
    "setProperties",
    OperationMode.Normal,
    None,
    (),
    (((), _Ice_PropertyDict_t, False, 0),),
    (),
    None,
    ())

__all__ = ["PropertiesAdmin", "PropertiesAdminPrx", "_Ice_PropertiesAdminPrx_t"]
