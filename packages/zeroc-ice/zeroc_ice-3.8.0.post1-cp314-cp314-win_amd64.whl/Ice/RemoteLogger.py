# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.LogMessage import _Ice_LogMessage_t

from Ice.LogMessageSeq import _Ice_LogMessageSeq_t

from Ice.Object import Object

from Ice.ObjectPrx import ObjectPrx
from Ice.ObjectPrx import checkedCast
from Ice.ObjectPrx import checkedCastAsync
from Ice.ObjectPrx import uncheckedCast

from Ice.OperationMode import OperationMode

from Ice.RemoteLogger_forward import _Ice_RemoteLoggerPrx_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from Ice.LogMessage import LogMessage
    from collections.abc import Awaitable
    from collections.abc import Sequence


class RemoteLoggerPrx(ObjectPrx):
    """
    Represents an Ice object that accepts log messages. It's called by the implementation of :class:`Ice.LoggerAdminPrx`.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::Ice::RemoteLogger``.
    """

    def init(self, prefix: str, logMessages: Sequence[LogMessage], context: dict[str, str] | None = None) -> None:
        """
        Attaches a remote logger to the local logger.
        
        Parameters
        ----------
        prefix : str
            The prefix of the associated local Logger.
        logMessages : Sequence[LogMessage]
            Old log messages generated before "now".
        context : dict[str, str]
            The request context for the invocation.
        """
        return RemoteLogger._op_init.invoke(self, ((prefix, logMessages), context))

    def initAsync(self, prefix: str, logMessages: Sequence[LogMessage], context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Attaches a remote logger to the local logger.
        
        Parameters
        ----------
        prefix : str
            The prefix of the associated local Logger.
        logMessages : Sequence[LogMessage]
            Old log messages generated before "now".
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return RemoteLogger._op_init.invokeAsync(self, ((prefix, logMessages), context))

    def log(self, message: LogMessage, context: dict[str, str] | None = None) -> None:
        """
        Logs a LogMessage.
        
        Parameters
        ----------
        message : LogMessage
            The message to log.
        context : dict[str, str]
            The request context for the invocation.
        
        Notes
        -----
            :meth:`Ice.RemoteLoggerPrx.logAsync` may be called by :class:`Ice.LoggerAdminPrx` before :meth:`Ice.RemoteLoggerPrx.initAsync`.
        """
        return RemoteLogger._op_log.invoke(self, ((message, ), context))

    def logAsync(self, message: LogMessage, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Logs a LogMessage.
        
        Parameters
        ----------
        message : LogMessage
            The message to log.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        
        Notes
        -----
            :meth:`Ice.RemoteLoggerPrx.logAsync` may be called by :class:`Ice.LoggerAdminPrx` before :meth:`Ice.RemoteLoggerPrx.initAsync`.
        """
        return RemoteLogger._op_log.invokeAsync(self, ((message, ), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> RemoteLoggerPrx | None:
        return checkedCast(RemoteLoggerPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[RemoteLoggerPrx | None ]:
        return checkedCastAsync(RemoteLoggerPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> RemoteLoggerPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> RemoteLoggerPrx | None:
        return uncheckedCast(RemoteLoggerPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::Ice::RemoteLogger"

IcePy.defineProxy("::Ice::RemoteLogger", RemoteLoggerPrx)

class RemoteLogger(Object, ABC):
    """
    Represents an Ice object that accepts log messages. It's called by the implementation of :class:`Ice.LoggerAdminPrx`.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::Ice::RemoteLogger``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::Ice::RemoteLogger", )
    _op_init: IcePy.Operation
    _op_log: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::Ice::RemoteLogger"

    @abstractmethod
    def init(self, prefix: str, logMessages: list[LogMessage], current: Current) -> None | Awaitable[None]:
        """
        Attaches a remote logger to the local logger.
        
        Parameters
        ----------
        prefix : str
            The prefix of the associated local Logger.
        logMessages : list[LogMessage]
            Old log messages generated before "now".
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        """
        pass

    @abstractmethod
    def log(self, message: LogMessage, current: Current) -> None | Awaitable[None]:
        """
        Logs a LogMessage.
        
        Parameters
        ----------
        message : LogMessage
            The message to log.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Notes
        -----
            :meth:`Ice.RemoteLoggerPrx.logAsync` may be called by :class:`Ice.LoggerAdminPrx` before :meth:`Ice.RemoteLoggerPrx.initAsync`.
        """
        pass

RemoteLogger._op_init = IcePy.Operation(
    "init",
    "init",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), _Ice_LogMessageSeq_t, False, 0)),
    (),
    None,
    ())

RemoteLogger._op_log = IcePy.Operation(
    "log",
    "log",
    OperationMode.Normal,
    None,
    (),
    (((), _Ice_LogMessage_t, False, 0),),
    (),
    None,
    ())

__all__ = ["RemoteLogger", "RemoteLoggerPrx", "_Ice_RemoteLoggerPrx_t"]
