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

from Ice.StringSeq import _Ice_StringSeq_t

from IceGrid.FileIterator_forward import _IceGrid_FileIteratorPrx_t

from IceGrid.FileNotAvailableException import _IceGrid_FileNotAvailableException_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from collections.abc import Awaitable
    from collections.abc import Sequence


class FileIteratorPrx(ObjectPrx):
    """
    Iterates over an IceGrid log file.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::IceGrid::FileIterator``.
    """

    def read(self, size: int, context: dict[str, str] | None = None) -> tuple[bool, list[str]]:
        """
        Read lines from the log file.
        
        Parameters
        ----------
        size : int
            Specifies the maximum number of bytes to be received. The server will ensure that the returned
            message doesn't exceed the given size.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        tuple[bool, list[str]]
        
            A tuple containing:
                - bool ``true`` if EOF is encountered.
                - list[str] The lines read from the file. If there was nothing to read from the file since the last call to
                  read, an empty sequence is returned. The last line of the sequence is always incomplete (and therefore no
                  newline character should be added when writing the last line to the to the output device).
        
        Raises
        ------
        FileNotAvailableException
            Thrown when the implementation failed to read from the file.
        """
        return FileIterator._op_read.invoke(self, ((size, ), context))

    def readAsync(self, size: int, context: dict[str, str] | None = None) -> Awaitable[tuple[bool, list[str]]]:
        """
        Read lines from the log file.
        
        Parameters
        ----------
        size : int
            Specifies the maximum number of bytes to be received. The server will ensure that the returned
            message doesn't exceed the given size.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[tuple[bool, list[str]]]
        
            A tuple containing:
                - bool ``true`` if EOF is encountered.
                - list[str] The lines read from the file. If there was nothing to read from the file since the last call to
                  read, an empty sequence is returned. The last line of the sequence is always incomplete (and therefore no
                  newline character should be added when writing the last line to the to the output device).
        """
        return FileIterator._op_read.invokeAsync(self, ((size, ), context))

    def destroy(self, context: dict[str, str] | None = None) -> None:
        """
        Destroys the iterator.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        """
        return FileIterator._op_destroy.invoke(self, ((), context))

    def destroyAsync(self, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Destroys the iterator.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return FileIterator._op_destroy.invokeAsync(self, ((), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> FileIteratorPrx | None:
        return checkedCast(FileIteratorPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[FileIteratorPrx | None ]:
        return checkedCastAsync(FileIteratorPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> FileIteratorPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> FileIteratorPrx | None:
        return uncheckedCast(FileIteratorPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::FileIterator"

IcePy.defineProxy("::IceGrid::FileIterator", FileIteratorPrx)

class FileIterator(Object, ABC):
    """
    Iterates over an IceGrid log file.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::IceGrid::FileIterator``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::IceGrid::FileIterator", )
    _op_read: IcePy.Operation
    _op_destroy: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::FileIterator"

    @abstractmethod
    def read(self, size: int, current: Current) -> tuple[bool, Sequence[str]] | Awaitable[tuple[bool, Sequence[str]]]:
        """
        Read lines from the log file.
        
        Parameters
        ----------
        size : int
            Specifies the maximum number of bytes to be received. The server will ensure that the returned
            message doesn't exceed the given size.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        tuple[bool, Sequence[str]] | Awaitable[tuple[bool, Sequence[str]]]
        
            A tuple containing:
                - bool ``true`` if EOF is encountered.
                - Sequence[str] The lines read from the file. If there was nothing to read from the file since the last call to
                  read, an empty sequence is returned. The last line of the sequence is always incomplete (and therefore no
                  newline character should be added when writing the last line to the to the output device).
        
        Raises
        ------
        FileNotAvailableException
            Thrown when the implementation failed to read from the file.
        """
        pass

    @abstractmethod
    def destroy(self, current: Current) -> None | Awaitable[None]:
        """
        Destroys the iterator.
        
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

FileIterator._op_read = IcePy.Operation(
    "read",
    "read",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_int, False, 0),),
    (((), _Ice_StringSeq_t, False, 0),),
    ((), IcePy._t_bool, False, 0),
    (_IceGrid_FileNotAvailableException_t,))

FileIterator._op_destroy = IcePy.Operation(
    "destroy",
    "destroy",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    None,
    ())

__all__ = ["FileIterator", "FileIteratorPrx", "_IceGrid_FileIteratorPrx_t"]
