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

from IceGrid.Admin_forward import _IceGrid_AdminPrx_t

from IceGrid.ApplicationDescriptor import _IceGrid_ApplicationDescriptor_t

from IceGrid.FileParser_forward import _IceGrid_FileParserPrx_t

from IceGrid.ParseException import _IceGrid_ParseException_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from IceGrid.Admin import AdminPrx
    from IceGrid.ApplicationDescriptor import ApplicationDescriptor
    from collections.abc import Awaitable
    from collections.abc import Sequence


class FileParserPrx(ObjectPrx):
    """
    ``icegridadmin`` provides a ``FileParser`` object to transform XML files into :class:`IceGrid.ApplicationDescriptor` objects.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::IceGrid::FileParser``.
    """

    def parse(self, xmlFile: str, adminProxy: AdminPrx | None, context: dict[str, str] | None = None) -> ApplicationDescriptor:
        """
        Parses a file.
        
        Parameters
        ----------
        xmlFile : str
            The full path to the file.
        adminProxy : AdminPrx | None
            An :class:`IceGrid.AdminPrx` proxy, used only to retrieve default templates when needed. May be null.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ApplicationDescriptor
            The application descriptor.
        
        Raises
        ------
        ParseException
            Thrown when an error occurs during parsing.
        """
        return FileParser._op_parse.invoke(self, ((xmlFile, adminProxy), context))

    def parseAsync(self, xmlFile: str, adminProxy: AdminPrx | None, context: dict[str, str] | None = None) -> Awaitable[ApplicationDescriptor]:
        """
        Parses a file.
        
        Parameters
        ----------
        xmlFile : str
            The full path to the file.
        adminProxy : AdminPrx | None
            An :class:`IceGrid.AdminPrx` proxy, used only to retrieve default templates when needed. May be null.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ApplicationDescriptor]
            The application descriptor.
        """
        return FileParser._op_parse.invokeAsync(self, ((xmlFile, adminProxy), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> FileParserPrx | None:
        return checkedCast(FileParserPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[FileParserPrx | None ]:
        return checkedCastAsync(FileParserPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> FileParserPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> FileParserPrx | None:
        return uncheckedCast(FileParserPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::FileParser"

IcePy.defineProxy("::IceGrid::FileParser", FileParserPrx)

class FileParser(Object, ABC):
    """
    ``icegridadmin`` provides a ``FileParser`` object to transform XML files into :class:`IceGrid.ApplicationDescriptor` objects.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::IceGrid::FileParser``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::IceGrid::FileParser", )
    _op_parse: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::FileParser"

    @abstractmethod
    def parse(self, xmlFile: str, adminProxy: AdminPrx | None, current: Current) -> ApplicationDescriptor | Awaitable[ApplicationDescriptor]:
        """
        Parses a file.
        
        Parameters
        ----------
        xmlFile : str
            The full path to the file.
        adminProxy : AdminPrx | None
            An :class:`IceGrid.AdminPrx` proxy, used only to retrieve default templates when needed. May be null.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ApplicationDescriptor | Awaitable[ApplicationDescriptor]
            The application descriptor.
        
        Raises
        ------
        ParseException
            Thrown when an error occurs during parsing.
        """
        pass

FileParser._op_parse = IcePy.Operation(
    "parse",
    "parse",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), _IceGrid_AdminPrx_t, False, 0)),
    (),
    ((), _IceGrid_ApplicationDescriptor_t, False, 0),
    (_IceGrid_ParseException_t,))

__all__ = ["FileParser", "FileParserPrx", "_IceGrid_FileParserPrx_t"]
