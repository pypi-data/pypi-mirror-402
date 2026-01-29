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

from Ice.Process_forward import _Ice_ProcessPrx_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from collections.abc import Awaitable
    from collections.abc import Sequence


class ProcessPrx(ObjectPrx):
    """
    A server application managed by a locator implementation such as IceGrid hosts a Process object and registers a
    proxy to this object with the locator registry. See :meth:`Ice.LocatorRegistryPrx.setServerProcessProxyAsync`.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::Ice::Process``.
    """

    def shutdown(self, context: dict[str, str] | None = None) -> None:
        """
        Initiates a graceful shutdown of the server application.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        """
        return Process._op_shutdown.invoke(self, ((), context))

    def shutdownAsync(self, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Initiates a graceful shutdown of the server application.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Process._op_shutdown.invokeAsync(self, ((), context))

    def writeMessage(self, message: str, fd: int, context: dict[str, str] | None = None) -> None:
        """
        Writes a message on the server application's stdout or stderr.
        
        Parameters
        ----------
        message : str
            The message to write.
        fd : int
            1 for stdout, 2 for stderr.
        context : dict[str, str]
            The request context for the invocation.
        """
        return Process._op_writeMessage.invoke(self, ((message, fd), context))

    def writeMessageAsync(self, message: str, fd: int, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Writes a message on the server application's stdout or stderr.
        
        Parameters
        ----------
        message : str
            The message to write.
        fd : int
            1 for stdout, 2 for stderr.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Process._op_writeMessage.invokeAsync(self, ((message, fd), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> ProcessPrx | None:
        return checkedCast(ProcessPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[ProcessPrx | None ]:
        return checkedCastAsync(ProcessPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> ProcessPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> ProcessPrx | None:
        return uncheckedCast(ProcessPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::Ice::Process"

IcePy.defineProxy("::Ice::Process", ProcessPrx)

class Process(Object, ABC):
    """
    A server application managed by a locator implementation such as IceGrid hosts a Process object and registers a
    proxy to this object with the locator registry. See :meth:`Ice.LocatorRegistryPrx.setServerProcessProxyAsync`.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::Ice::Process``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::Ice::Process", )
    _op_shutdown: IcePy.Operation
    _op_writeMessage: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::Ice::Process"

    @abstractmethod
    def shutdown(self, current: Current) -> None | Awaitable[None]:
        """
        Initiates a graceful shutdown of the server application.
        
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
    def writeMessage(self, message: str, fd: int, current: Current) -> None | Awaitable[None]:
        """
        Writes a message on the server application's stdout or stderr.
        
        Parameters
        ----------
        message : str
            The message to write.
        fd : int
            1 for stdout, 2 for stderr.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

Process._op_shutdown = IcePy.Operation(
    "shutdown",
    "shutdown",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    None,
    ())

Process._op_writeMessage = IcePy.Operation(
    "writeMessage",
    "writeMessage",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), IcePy._t_int, False, 0)),
    (),
    None,
    ())

__all__ = ["Process", "ProcessPrx", "_Ice_ProcessPrx_t"]
