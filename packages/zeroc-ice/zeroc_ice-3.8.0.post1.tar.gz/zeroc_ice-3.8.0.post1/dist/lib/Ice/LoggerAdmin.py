# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.LogMessageSeq import _Ice_LogMessageSeq_t

from Ice.LogMessageTypeSeq import _Ice_LogMessageTypeSeq_t

from Ice.LoggerAdmin_forward import _Ice_LoggerAdminPrx_t

from Ice.Object import Object

from Ice.ObjectPrx import ObjectPrx
from Ice.ObjectPrx import checkedCast
from Ice.ObjectPrx import checkedCastAsync
from Ice.ObjectPrx import uncheckedCast

from Ice.OperationMode import OperationMode

from Ice.RemoteLoggerAlreadyAttachedException import _Ice_RemoteLoggerAlreadyAttachedException_t

from Ice.RemoteLogger_forward import _Ice_RemoteLoggerPrx_t

from Ice.StringSeq import _Ice_StringSeq_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from Ice.LogMessage import LogMessage
    from Ice.LogMessageType import LogMessageType
    from Ice.RemoteLogger import RemoteLoggerPrx
    from collections.abc import Awaitable
    from collections.abc import Sequence


class LoggerAdminPrx(ObjectPrx):
    """
    Represents the admin facet that allows an Ice application to attach its :class:`Ice.RemoteLoggerPrx` to the local
    logger of an Ice communicator.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::Ice::LoggerAdmin``.
    """

    def attachRemoteLogger(self, prx: RemoteLoggerPrx | None, messageTypes: Sequence[LogMessageType], traceCategories: Sequence[str], messageMax: int, context: dict[str, str] | None = None) -> None:
        """
        Attaches a :class:`Ice.RemoteLoggerPrx` object to the local logger. This operation calls :meth:`Ice.RemoteLoggerPrx.initAsync`
        on ``prx``.
        
        Parameters
        ----------
        prx : RemoteLoggerPrx | None
            A proxy to the remote logger.
        messageTypes : Sequence[LogMessageType]
            The list of message types that the remote logger wishes to receive. An empty list means
            no filtering (send all message types).
        traceCategories : Sequence[str]
            The categories of traces that the remote logger wishes to receive. This parameter is
            ignored if ``messageTypes`` is not empty and does not include trace. An empty list means no filtering
            (send all trace categories).
        messageMax : int
            The maximum number of log messages (of all types) to be provided to
            :meth:`Ice.RemoteLoggerPrx.initAsync`. A negative value requests all messages available.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        RemoteLoggerAlreadyAttachedException
            Thrown if this remote logger is already attached to this admin
            object.
        """
        return LoggerAdmin._op_attachRemoteLogger.invoke(self, ((prx, messageTypes, traceCategories, messageMax), context))

    def attachRemoteLoggerAsync(self, prx: RemoteLoggerPrx | None, messageTypes: Sequence[LogMessageType], traceCategories: Sequence[str], messageMax: int, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Attaches a :class:`Ice.RemoteLoggerPrx` object to the local logger. This operation calls :meth:`Ice.RemoteLoggerPrx.initAsync`
        on ``prx``.
        
        Parameters
        ----------
        prx : RemoteLoggerPrx | None
            A proxy to the remote logger.
        messageTypes : Sequence[LogMessageType]
            The list of message types that the remote logger wishes to receive. An empty list means
            no filtering (send all message types).
        traceCategories : Sequence[str]
            The categories of traces that the remote logger wishes to receive. This parameter is
            ignored if ``messageTypes`` is not empty and does not include trace. An empty list means no filtering
            (send all trace categories).
        messageMax : int
            The maximum number of log messages (of all types) to be provided to
            :meth:`Ice.RemoteLoggerPrx.initAsync`. A negative value requests all messages available.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return LoggerAdmin._op_attachRemoteLogger.invokeAsync(self, ((prx, messageTypes, traceCategories, messageMax), context))

    def detachRemoteLogger(self, prx: RemoteLoggerPrx | None, context: dict[str, str] | None = None) -> bool:
        """
        Detaches a :class:`Ice.RemoteLoggerPrx` object from the local logger.
        
        Parameters
        ----------
        prx : RemoteLoggerPrx | None
            A proxy to the remote logger.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        bool
            ``true`` if the provided remote logger proxy was detached, and ``false`` otherwise.
        """
        return LoggerAdmin._op_detachRemoteLogger.invoke(self, ((prx, ), context))

    def detachRemoteLoggerAsync(self, prx: RemoteLoggerPrx | None, context: dict[str, str] | None = None) -> Awaitable[bool]:
        """
        Detaches a :class:`Ice.RemoteLoggerPrx` object from the local logger.
        
        Parameters
        ----------
        prx : RemoteLoggerPrx | None
            A proxy to the remote logger.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[bool]
            ``true`` if the provided remote logger proxy was detached, and ``false`` otherwise.
        """
        return LoggerAdmin._op_detachRemoteLogger.invokeAsync(self, ((prx, ), context))

    def getLog(self, messageTypes: Sequence[LogMessageType], traceCategories: Sequence[str], messageMax: int, context: dict[str, str] | None = None) -> tuple[list[LogMessage], str]:
        """
        Retrieves recently logged log messages.
        
        Parameters
        ----------
        messageTypes : Sequence[LogMessageType]
            The list of message types that the caller wishes to receive. An empty list means no
            filtering (send all message types).
        traceCategories : Sequence[str]
            The categories of traces that caller wish to receive. This parameter is ignored if
            ``messageTypes`` is not empty and does not include trace. An empty list means no filtering (send all trace
            categories).
        messageMax : int
            The maximum number of log messages (of all types) to be returned. A negative value
            requests all messages available.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        tuple[list[LogMessage], str]
        
            A tuple containing:
                - list[LogMessage] The Log messages.
                - str The prefix of the associated local logger.
        """
        return LoggerAdmin._op_getLog.invoke(self, ((messageTypes, traceCategories, messageMax), context))

    def getLogAsync(self, messageTypes: Sequence[LogMessageType], traceCategories: Sequence[str], messageMax: int, context: dict[str, str] | None = None) -> Awaitable[tuple[list[LogMessage], str]]:
        """
        Retrieves recently logged log messages.
        
        Parameters
        ----------
        messageTypes : Sequence[LogMessageType]
            The list of message types that the caller wishes to receive. An empty list means no
            filtering (send all message types).
        traceCategories : Sequence[str]
            The categories of traces that caller wish to receive. This parameter is ignored if
            ``messageTypes`` is not empty and does not include trace. An empty list means no filtering (send all trace
            categories).
        messageMax : int
            The maximum number of log messages (of all types) to be returned. A negative value
            requests all messages available.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[tuple[list[LogMessage], str]]
        
            A tuple containing:
                - list[LogMessage] The Log messages.
                - str The prefix of the associated local logger.
        """
        return LoggerAdmin._op_getLog.invokeAsync(self, ((messageTypes, traceCategories, messageMax), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> LoggerAdminPrx | None:
        return checkedCast(LoggerAdminPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[LoggerAdminPrx | None ]:
        return checkedCastAsync(LoggerAdminPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> LoggerAdminPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> LoggerAdminPrx | None:
        return uncheckedCast(LoggerAdminPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::Ice::LoggerAdmin"

IcePy.defineProxy("::Ice::LoggerAdmin", LoggerAdminPrx)

class LoggerAdmin(Object, ABC):
    """
    Represents the admin facet that allows an Ice application to attach its :class:`Ice.RemoteLoggerPrx` to the local
    logger of an Ice communicator.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::Ice::LoggerAdmin``.
    """

    _ice_ids: Sequence[str] = ("::Ice::LoggerAdmin", "::Ice::Object", )
    _op_attachRemoteLogger: IcePy.Operation
    _op_detachRemoteLogger: IcePy.Operation
    _op_getLog: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::Ice::LoggerAdmin"

    @abstractmethod
    def attachRemoteLogger(self, prx: RemoteLoggerPrx | None, messageTypes: list[LogMessageType], traceCategories: list[str], messageMax: int, current: Current) -> None | Awaitable[None]:
        """
        Attaches a :class:`Ice.RemoteLoggerPrx` object to the local logger. This operation calls :meth:`Ice.RemoteLoggerPrx.initAsync`
        on ``prx``.
        
        Parameters
        ----------
        prx : RemoteLoggerPrx | None
            A proxy to the remote logger.
        messageTypes : list[LogMessageType]
            The list of message types that the remote logger wishes to receive. An empty list means
            no filtering (send all message types).
        traceCategories : list[str]
            The categories of traces that the remote logger wishes to receive. This parameter is
            ignored if ``messageTypes`` is not empty and does not include trace. An empty list means no filtering
            (send all trace categories).
        messageMax : int
            The maximum number of log messages (of all types) to be provided to
            :meth:`Ice.RemoteLoggerPrx.initAsync`. A negative value requests all messages available.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        RemoteLoggerAlreadyAttachedException
            Thrown if this remote logger is already attached to this admin
            object.
        """
        pass

    @abstractmethod
    def detachRemoteLogger(self, prx: RemoteLoggerPrx | None, current: Current) -> bool | Awaitable[bool]:
        """
        Detaches a :class:`Ice.RemoteLoggerPrx` object from the local logger.
        
        Parameters
        ----------
        prx : RemoteLoggerPrx | None
            A proxy to the remote logger.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        bool | Awaitable[bool]
            ``true`` if the provided remote logger proxy was detached, and ``false`` otherwise.
        """
        pass

    @abstractmethod
    def getLog(self, messageTypes: list[LogMessageType], traceCategories: list[str], messageMax: int, current: Current) -> tuple[Sequence[LogMessage], str] | Awaitable[tuple[Sequence[LogMessage], str]]:
        """
        Retrieves recently logged log messages.
        
        Parameters
        ----------
        messageTypes : list[LogMessageType]
            The list of message types that the caller wishes to receive. An empty list means no
            filtering (send all message types).
        traceCategories : list[str]
            The categories of traces that caller wish to receive. This parameter is ignored if
            ``messageTypes`` is not empty and does not include trace. An empty list means no filtering (send all trace
            categories).
        messageMax : int
            The maximum number of log messages (of all types) to be returned. A negative value
            requests all messages available.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        tuple[Sequence[LogMessage], str] | Awaitable[tuple[Sequence[LogMessage], str]]
        
            A tuple containing:
                - Sequence[LogMessage] The Log messages.
                - str The prefix of the associated local logger.
        """
        pass

LoggerAdmin._op_attachRemoteLogger = IcePy.Operation(
    "attachRemoteLogger",
    "attachRemoteLogger",
    OperationMode.Normal,
    None,
    (),
    (((), _Ice_RemoteLoggerPrx_t, False, 0), ((), _Ice_LogMessageTypeSeq_t, False, 0), ((), _Ice_StringSeq_t, False, 0), ((), IcePy._t_int, False, 0)),
    (),
    None,
    (_Ice_RemoteLoggerAlreadyAttachedException_t,))

LoggerAdmin._op_detachRemoteLogger = IcePy.Operation(
    "detachRemoteLogger",
    "detachRemoteLogger",
    OperationMode.Normal,
    None,
    (),
    (((), _Ice_RemoteLoggerPrx_t, False, 0),),
    (),
    ((), IcePy._t_bool, False, 0),
    ())

LoggerAdmin._op_getLog = IcePy.Operation(
    "getLog",
    "getLog",
    OperationMode.Normal,
    None,
    (),
    (((), _Ice_LogMessageTypeSeq_t, False, 0), ((), _Ice_StringSeq_t, False, 0), ((), IcePy._t_int, False, 0)),
    (((), IcePy._t_string, False, 0),),
    ((), _Ice_LogMessageSeq_t, False, 0),
    ())

__all__ = ["LoggerAdmin", "LoggerAdminPrx", "_Ice_LoggerAdminPrx_t"]
