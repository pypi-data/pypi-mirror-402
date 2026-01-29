# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Glacier2.Session import Session
from Glacier2.Session import SessionPrx

from Ice.Identity import _Ice_Identity_t

from Ice.ObjectPrx import checkedCast
from Ice.ObjectPrx import checkedCastAsync
from Ice.ObjectPrx import uncheckedCast

from Ice.ObjectPrx_forward import _Ice_ObjectPrx_t

from Ice.OperationMode import OperationMode

from IceGrid.AccessDeniedException import _IceGrid_AccessDeniedException_t

from IceGrid.AdapterObserver_forward import _IceGrid_AdapterObserverPrx_t

from IceGrid.AdminSession_forward import _IceGrid_AdminSessionPrx_t

from IceGrid.Admin_forward import _IceGrid_AdminPrx_t

from IceGrid.ApplicationObserver_forward import _IceGrid_ApplicationObserverPrx_t

from IceGrid.DeploymentException import _IceGrid_DeploymentException_t

from IceGrid.FileIterator_forward import _IceGrid_FileIteratorPrx_t

from IceGrid.FileNotAvailableException import _IceGrid_FileNotAvailableException_t

from IceGrid.NodeNotExistException import _IceGrid_NodeNotExistException_t

from IceGrid.NodeObserver_forward import _IceGrid_NodeObserverPrx_t

from IceGrid.NodeUnreachableException import _IceGrid_NodeUnreachableException_t

from IceGrid.ObjectObserver_forward import _IceGrid_ObjectObserverPrx_t

from IceGrid.ObserverAlreadyRegisteredException import _IceGrid_ObserverAlreadyRegisteredException_t

from IceGrid.RegistryNotExistException import _IceGrid_RegistryNotExistException_t

from IceGrid.RegistryObserver_forward import _IceGrid_RegistryObserverPrx_t

from IceGrid.RegistryUnreachableException import _IceGrid_RegistryUnreachableException_t

from IceGrid.ServerNotExistException import _IceGrid_ServerNotExistException_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from Ice.Identity import Identity
    from Ice.ObjectPrx import ObjectPrx
    from IceGrid.AdapterObserver import AdapterObserverPrx
    from IceGrid.Admin import AdminPrx
    from IceGrid.ApplicationObserver import ApplicationObserverPrx
    from IceGrid.FileIterator import FileIteratorPrx
    from IceGrid.NodeObserver import NodeObserverPrx
    from IceGrid.ObjectObserver import ObjectObserverPrx
    from IceGrid.RegistryObserver import RegistryObserverPrx
    from collections.abc import Awaitable
    from collections.abc import Sequence


class AdminSessionPrx(SessionPrx):
    """
    Represents an administrative session between an admin tool and an IceGrid registry.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::IceGrid::AdminSession``.
    
    See Also
    --------
        :class:`IceGrid.RegistryPrx`
    """

    def keepAlive(self, context: dict[str, str] | None = None) -> None:
        """
        Keeps the session alive.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        """
        return AdminSession._op_keepAlive.invoke(self, ((), context))

    def keepAliveAsync(self, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Keeps the session alive.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return AdminSession._op_keepAlive.invokeAsync(self, ((), context))

    def getAdmin(self, context: dict[str, str] | None = None) -> AdminPrx | None:
        """
        Gets a proxy to the IceGrid admin object. The admin object returned by this operation can only be accessed
        by the session.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        AdminPrx | None
            A proxy to the IceGrid admin object. This proxy is never null.
        """
        return AdminSession._op_getAdmin.invoke(self, ((), context))

    def getAdminAsync(self, context: dict[str, str] | None = None) -> Awaitable[AdminPrx | None]:
        """
        Gets a proxy to the IceGrid admin object. The admin object returned by this operation can only be accessed
        by the session.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[AdminPrx | None]
            A proxy to the IceGrid admin object. This proxy is never null.
        """
        return AdminSession._op_getAdmin.invokeAsync(self, ((), context))

    def getAdminCallbackTemplate(self, context: dict[str, str] | None = None) -> ObjectPrx | None:
        """
        Gets a "template" proxy for admin callback objects. An Admin client uses this proxy to set the category of
        its callback objects, and the published endpoints of the object adapter hosting the admin callback objects.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ObjectPrx | None
            A template proxy. The returned proxy is null when the Admin session was established using Glacier2.
        """
        return AdminSession._op_getAdminCallbackTemplate.invoke(self, ((), context))

    def getAdminCallbackTemplateAsync(self, context: dict[str, str] | None = None) -> Awaitable[ObjectPrx | None]:
        """
        Gets a "template" proxy for admin callback objects. An Admin client uses this proxy to set the category of
        its callback objects, and the published endpoints of the object adapter hosting the admin callback objects.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ObjectPrx | None]
            A template proxy. The returned proxy is null when the Admin session was established using Glacier2.
        """
        return AdminSession._op_getAdminCallbackTemplate.invokeAsync(self, ((), context))

    def setObservers(self, registryObs: RegistryObserverPrx | None, nodeObs: NodeObserverPrx | None, appObs: ApplicationObserverPrx | None, adptObs: AdapterObserverPrx | None, objObs: ObjectObserverPrx | None, context: dict[str, str] | None = None) -> None:
        """
        Sets the observer proxies that receive notifications when the state of the registry or nodes changes.
        
        Parameters
        ----------
        registryObs : RegistryObserverPrx | None
            The registry observer.
        nodeObs : NodeObserverPrx | None
            The node observer.
        appObs : ApplicationObserverPrx | None
            The application observer.
        adptObs : AdapterObserverPrx | None
            The adapter observer.
        objObs : ObjectObserverPrx | None
            The object observer.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        ObserverAlreadyRegisteredException
            Thrown when an observer is already registered with this registry.
        """
        return AdminSession._op_setObservers.invoke(self, ((registryObs, nodeObs, appObs, adptObs, objObs), context))

    def setObserversAsync(self, registryObs: RegistryObserverPrx | None, nodeObs: NodeObserverPrx | None, appObs: ApplicationObserverPrx | None, adptObs: AdapterObserverPrx | None, objObs: ObjectObserverPrx | None, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Sets the observer proxies that receive notifications when the state of the registry or nodes changes.
        
        Parameters
        ----------
        registryObs : RegistryObserverPrx | None
            The registry observer.
        nodeObs : NodeObserverPrx | None
            The node observer.
        appObs : ApplicationObserverPrx | None
            The application observer.
        adptObs : AdapterObserverPrx | None
            The adapter observer.
        objObs : ObjectObserverPrx | None
            The object observer.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return AdminSession._op_setObservers.invokeAsync(self, ((registryObs, nodeObs, appObs, adptObs, objObs), context))

    def setObserversByIdentity(self, registryObs: Identity, nodeObs: Identity, appObs: Identity, adptObs: Identity, objObs: Identity, context: dict[str, str] | None = None) -> None:
        """
        Sets the observer identities that receive notifications when the state of the registry or nodes changes.
        This operation should be used by clients that are using a bidirectional connection to communicate with the
        session.
        
        Parameters
        ----------
        registryObs : Identity
            The registry observer identity.
        nodeObs : Identity
            The node observer identity.
        appObs : Identity
            The application observer.
        adptObs : Identity
            The adapter observer.
        objObs : Identity
            The object observer.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        ObserverAlreadyRegisteredException
            Thrown when an observer is already registered with this registry.
        """
        return AdminSession._op_setObserversByIdentity.invoke(self, ((registryObs, nodeObs, appObs, adptObs, objObs), context))

    def setObserversByIdentityAsync(self, registryObs: Identity, nodeObs: Identity, appObs: Identity, adptObs: Identity, objObs: Identity, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Sets the observer identities that receive notifications when the state of the registry or nodes changes.
        This operation should be used by clients that are using a bidirectional connection to communicate with the
        session.
        
        Parameters
        ----------
        registryObs : Identity
            The registry observer identity.
        nodeObs : Identity
            The node observer identity.
        appObs : Identity
            The application observer.
        adptObs : Identity
            The adapter observer.
        objObs : Identity
            The object observer.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return AdminSession._op_setObserversByIdentity.invokeAsync(self, ((registryObs, nodeObs, appObs, adptObs, objObs), context))

    def startUpdate(self, context: dict[str, str] | None = None) -> int:
        """
        Acquires an exclusive lock to start updating the registry applications.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        int
            The current serial.
        
        Raises
        ------
        AccessDeniedException
            Thrown when the exclusive lock can't be acquired. This might happen if the
            lock is currently acquired by another session.
        """
        return AdminSession._op_startUpdate.invoke(self, ((), context))

    def startUpdateAsync(self, context: dict[str, str] | None = None) -> Awaitable[int]:
        """
        Acquires an exclusive lock to start updating the registry applications.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[int]
            The current serial.
        """
        return AdminSession._op_startUpdate.invokeAsync(self, ((), context))

    def finishUpdate(self, context: dict[str, str] | None = None) -> None:
        """
        Finishes updating the registry and releases the exclusive lock.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        AccessDeniedException
            Thrown when the session doesn't hold the exclusive lock.
        """
        return AdminSession._op_finishUpdate.invoke(self, ((), context))

    def finishUpdateAsync(self, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Finishes updating the registry and releases the exclusive lock.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return AdminSession._op_finishUpdate.invokeAsync(self, ((), context))

    def getReplicaName(self, context: dict[str, str] | None = None) -> str:
        """
        Gets the name of the registry replica hosting this session.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        str
            The replica name of the registry.
        """
        return AdminSession._op_getReplicaName.invoke(self, ((), context))

    def getReplicaNameAsync(self, context: dict[str, str] | None = None) -> Awaitable[str]:
        """
        Gets the name of the registry replica hosting this session.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[str]
            The replica name of the registry.
        """
        return AdminSession._op_getReplicaName.invokeAsync(self, ((), context))

    def openServerLog(self, id: str, path: str, count: int, context: dict[str, str] | None = None) -> FileIteratorPrx | None:
        """
        Opens a server log file for reading.
        
        Parameters
        ----------
        id : str
            The server ID.
        path : str
            The path of the log file. A log file can be opened only if it's declared in the server or
            service deployment descriptor.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        FileIteratorPrx | None
            An iterator to read the file. This proxy is never null.
        
        Raises
        ------
        DeploymentException
            Thrown when the server couldn't be deployed on the node.
        FileNotAvailableException
            Thrown when the file can't be read.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        return AdminSession._op_openServerLog.invoke(self, ((id, path, count), context))

    def openServerLogAsync(self, id: str, path: str, count: int, context: dict[str, str] | None = None) -> Awaitable[FileIteratorPrx | None]:
        """
        Opens a server log file for reading.
        
        Parameters
        ----------
        id : str
            The server ID.
        path : str
            The path of the log file. A log file can be opened only if it's declared in the server or
            service deployment descriptor.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[FileIteratorPrx | None]
            An iterator to read the file. This proxy is never null.
        """
        return AdminSession._op_openServerLog.invokeAsync(self, ((id, path, count), context))

    def openServerStdErr(self, id: str, count: int, context: dict[str, str] | None = None) -> FileIteratorPrx | None:
        """
        Opens a server stderr file for reading.
        
        Parameters
        ----------
        id : str
            The server ID.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        FileIteratorPrx | None
            An iterator to read the file. This proxy is never null.
        
        Raises
        ------
        DeploymentException
            Thrown when the server couldn't be deployed on the node.
        FileNotAvailableException
            Thrown when the file can't be read.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        return AdminSession._op_openServerStdErr.invoke(self, ((id, count), context))

    def openServerStdErrAsync(self, id: str, count: int, context: dict[str, str] | None = None) -> Awaitable[FileIteratorPrx | None]:
        """
        Opens a server stderr file for reading.
        
        Parameters
        ----------
        id : str
            The server ID.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[FileIteratorPrx | None]
            An iterator to read the file. This proxy is never null.
        """
        return AdminSession._op_openServerStdErr.invokeAsync(self, ((id, count), context))

    def openServerStdOut(self, id: str, count: int, context: dict[str, str] | None = None) -> FileIteratorPrx | None:
        """
        Opens a server stdout file for reading.
        
        Parameters
        ----------
        id : str
            The server id.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        FileIteratorPrx | None
            An iterator to read the file. This proxy is never null.
        
        Raises
        ------
        DeploymentException
            Thrown when the server couldn't be deployed on the node.
        FileNotAvailableException
            Thrown when the file can't be read.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        return AdminSession._op_openServerStdOut.invoke(self, ((id, count), context))

    def openServerStdOutAsync(self, id: str, count: int, context: dict[str, str] | None = None) -> Awaitable[FileIteratorPrx | None]:
        """
        Opens a server stdout file for reading.
        
        Parameters
        ----------
        id : str
            The server id.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[FileIteratorPrx | None]
            An iterator to read the file. This proxy is never null.
        """
        return AdminSession._op_openServerStdOut.invokeAsync(self, ((id, count), context))

    def openNodeStdErr(self, name: str, count: int, context: dict[str, str] | None = None) -> FileIteratorPrx | None:
        """
        Opens a node stderr file for reading.
        
        Parameters
        ----------
        name : str
            The node name.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        FileIteratorPrx | None
            An iterator to read the file. This proxy is never null.
        
        Raises
        ------
        FileNotAvailableException
            Thrown when the file can't be read.
        NodeNotExistException
            Thrown when the node doesn't exist.
        NodeUnreachableException
            Thrown when the node is unreachable.
        """
        return AdminSession._op_openNodeStdErr.invoke(self, ((name, count), context))

    def openNodeStdErrAsync(self, name: str, count: int, context: dict[str, str] | None = None) -> Awaitable[FileIteratorPrx | None]:
        """
        Opens a node stderr file for reading.
        
        Parameters
        ----------
        name : str
            The node name.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[FileIteratorPrx | None]
            An iterator to read the file. This proxy is never null.
        """
        return AdminSession._op_openNodeStdErr.invokeAsync(self, ((name, count), context))

    def openNodeStdOut(self, name: str, count: int, context: dict[str, str] | None = None) -> FileIteratorPrx | None:
        """
        Opens a node stdout file for reading.
        
        Parameters
        ----------
        name : str
            The node name.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        FileIteratorPrx | None
            An iterator to read the file. This proxy is never null.
        
        Raises
        ------
        FileNotAvailableException
            Thrown when the file can't be read.
        NodeNotExistException
            Thrown when the node doesn't exist.
        NodeUnreachableException
            Thrown when the node is unreachable.
        """
        return AdminSession._op_openNodeStdOut.invoke(self, ((name, count), context))

    def openNodeStdOutAsync(self, name: str, count: int, context: dict[str, str] | None = None) -> Awaitable[FileIteratorPrx | None]:
        """
        Opens a node stdout file for reading.
        
        Parameters
        ----------
        name : str
            The node name.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[FileIteratorPrx | None]
            An iterator to read the file. This proxy is never null.
        """
        return AdminSession._op_openNodeStdOut.invokeAsync(self, ((name, count), context))

    def openRegistryStdErr(self, name: str, count: int, context: dict[str, str] | None = None) -> FileIteratorPrx | None:
        """
        Opens a registry stderr file for reading.
        
        Parameters
        ----------
        name : str
            The registry name.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        FileIteratorPrx | None
            An iterator to read the file. This proxy is never null.
        
        Raises
        ------
        FileNotAvailableException
            Thrown when the file can't be read.
        RegistryNotExistException
            Thrown when the registry doesn't exist.
        RegistryUnreachableException
            Thrown when the registry is unreachable.
        """
        return AdminSession._op_openRegistryStdErr.invoke(self, ((name, count), context))

    def openRegistryStdErrAsync(self, name: str, count: int, context: dict[str, str] | None = None) -> Awaitable[FileIteratorPrx | None]:
        """
        Opens a registry stderr file for reading.
        
        Parameters
        ----------
        name : str
            The registry name.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[FileIteratorPrx | None]
            An iterator to read the file. This proxy is never null.
        """
        return AdminSession._op_openRegistryStdErr.invokeAsync(self, ((name, count), context))

    def openRegistryStdOut(self, name: str, count: int, context: dict[str, str] | None = None) -> FileIteratorPrx | None:
        """
        Opens a registry stdout file for reading.
        
        Parameters
        ----------
        name : str
            The registry name.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        FileIteratorPrx | None
            An iterator to read the file. This proxy is never null.
        
        Raises
        ------
        FileNotAvailableException
            Thrown when the file can't be read.
        RegistryNotExistException
            Thrown when the registry doesn't exist.
        RegistryUnreachableException
            Thrown when the registry is unreachable.
        """
        return AdminSession._op_openRegistryStdOut.invoke(self, ((name, count), context))

    def openRegistryStdOutAsync(self, name: str, count: int, context: dict[str, str] | None = None) -> Awaitable[FileIteratorPrx | None]:
        """
        Opens a registry stdout file for reading.
        
        Parameters
        ----------
        name : str
            The registry name.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[FileIteratorPrx | None]
            An iterator to read the file. This proxy is never null.
        """
        return AdminSession._op_openRegistryStdOut.invokeAsync(self, ((name, count), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> AdminSessionPrx | None:
        return checkedCast(AdminSessionPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[AdminSessionPrx | None ]:
        return checkedCastAsync(AdminSessionPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> AdminSessionPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> AdminSessionPrx | None:
        return uncheckedCast(AdminSessionPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::AdminSession"

IcePy.defineProxy("::IceGrid::AdminSession", AdminSessionPrx)

class AdminSession(Session, ABC):
    """
    Represents an administrative session between an admin tool and an IceGrid registry.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::IceGrid::AdminSession``.
    
    See Also
    --------
        :class:`IceGrid.RegistryPrx`
    """

    _ice_ids: Sequence[str] = ("::Glacier2::Session", "::Ice::Object", "::IceGrid::AdminSession", )
    _op_keepAlive: IcePy.Operation
    _op_getAdmin: IcePy.Operation
    _op_getAdminCallbackTemplate: IcePy.Operation
    _op_setObservers: IcePy.Operation
    _op_setObserversByIdentity: IcePy.Operation
    _op_startUpdate: IcePy.Operation
    _op_finishUpdate: IcePy.Operation
    _op_getReplicaName: IcePy.Operation
    _op_openServerLog: IcePy.Operation
    _op_openServerStdErr: IcePy.Operation
    _op_openServerStdOut: IcePy.Operation
    _op_openNodeStdErr: IcePy.Operation
    _op_openNodeStdOut: IcePy.Operation
    _op_openRegistryStdErr: IcePy.Operation
    _op_openRegistryStdOut: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::AdminSession"

    @abstractmethod
    def keepAlive(self, current: Current) -> None | Awaitable[None]:
        """
        Keeps the session alive.
        
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
    def getAdmin(self, current: Current) -> AdminPrx | None | Awaitable[AdminPrx | None]:
        """
        Gets a proxy to the IceGrid admin object. The admin object returned by this operation can only be accessed
        by the session.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        AdminPrx | None | Awaitable[AdminPrx | None]
            A proxy to the IceGrid admin object. This proxy is never null.
        """
        pass

    @abstractmethod
    def getAdminCallbackTemplate(self, current: Current) -> ObjectPrx | None | Awaitable[ObjectPrx | None]:
        """
        Gets a "template" proxy for admin callback objects. An Admin client uses this proxy to set the category of
        its callback objects, and the published endpoints of the object adapter hosting the admin callback objects.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ObjectPrx | None | Awaitable[ObjectPrx | None]
            A template proxy. The returned proxy is null when the Admin session was established using Glacier2.
        """
        pass

    @abstractmethod
    def setObservers(self, registryObs: RegistryObserverPrx | None, nodeObs: NodeObserverPrx | None, appObs: ApplicationObserverPrx | None, adptObs: AdapterObserverPrx | None, objObs: ObjectObserverPrx | None, current: Current) -> None | Awaitable[None]:
        """
        Sets the observer proxies that receive notifications when the state of the registry or nodes changes.
        
        Parameters
        ----------
        registryObs : RegistryObserverPrx | None
            The registry observer.
        nodeObs : NodeObserverPrx | None
            The node observer.
        appObs : ApplicationObserverPrx | None
            The application observer.
        adptObs : AdapterObserverPrx | None
            The adapter observer.
        objObs : ObjectObserverPrx | None
            The object observer.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        ObserverAlreadyRegisteredException
            Thrown when an observer is already registered with this registry.
        """
        pass

    @abstractmethod
    def setObserversByIdentity(self, registryObs: Identity, nodeObs: Identity, appObs: Identity, adptObs: Identity, objObs: Identity, current: Current) -> None | Awaitable[None]:
        """
        Sets the observer identities that receive notifications when the state of the registry or nodes changes.
        This operation should be used by clients that are using a bidirectional connection to communicate with the
        session.
        
        Parameters
        ----------
        registryObs : Identity
            The registry observer identity.
        nodeObs : Identity
            The node observer identity.
        appObs : Identity
            The application observer.
        adptObs : Identity
            The adapter observer.
        objObs : Identity
            The object observer.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        ObserverAlreadyRegisteredException
            Thrown when an observer is already registered with this registry.
        """
        pass

    @abstractmethod
    def startUpdate(self, current: Current) -> int | Awaitable[int]:
        """
        Acquires an exclusive lock to start updating the registry applications.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        int | Awaitable[int]
            The current serial.
        
        Raises
        ------
        AccessDeniedException
            Thrown when the exclusive lock can't be acquired. This might happen if the
            lock is currently acquired by another session.
        """
        pass

    @abstractmethod
    def finishUpdate(self, current: Current) -> None | Awaitable[None]:
        """
        Finishes updating the registry and releases the exclusive lock.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        AccessDeniedException
            Thrown when the session doesn't hold the exclusive lock.
        """
        pass

    @abstractmethod
    def getReplicaName(self, current: Current) -> str | Awaitable[str]:
        """
        Gets the name of the registry replica hosting this session.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        str | Awaitable[str]
            The replica name of the registry.
        """
        pass

    @abstractmethod
    def openServerLog(self, id: str, path: str, count: int, current: Current) -> FileIteratorPrx | None | Awaitable[FileIteratorPrx | None]:
        """
        Opens a server log file for reading.
        
        Parameters
        ----------
        id : str
            The server ID.
        path : str
            The path of the log file. A log file can be opened only if it's declared in the server or
            service deployment descriptor.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        FileIteratorPrx | None | Awaitable[FileIteratorPrx | None]
            An iterator to read the file. This proxy is never null.
        
        Raises
        ------
        DeploymentException
            Thrown when the server couldn't be deployed on the node.
        FileNotAvailableException
            Thrown when the file can't be read.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        pass

    @abstractmethod
    def openServerStdErr(self, id: str, count: int, current: Current) -> FileIteratorPrx | None | Awaitable[FileIteratorPrx | None]:
        """
        Opens a server stderr file for reading.
        
        Parameters
        ----------
        id : str
            The server ID.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        FileIteratorPrx | None | Awaitable[FileIteratorPrx | None]
            An iterator to read the file. This proxy is never null.
        
        Raises
        ------
        DeploymentException
            Thrown when the server couldn't be deployed on the node.
        FileNotAvailableException
            Thrown when the file can't be read.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        pass

    @abstractmethod
    def openServerStdOut(self, id: str, count: int, current: Current) -> FileIteratorPrx | None | Awaitable[FileIteratorPrx | None]:
        """
        Opens a server stdout file for reading.
        
        Parameters
        ----------
        id : str
            The server id.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        FileIteratorPrx | None | Awaitable[FileIteratorPrx | None]
            An iterator to read the file. This proxy is never null.
        
        Raises
        ------
        DeploymentException
            Thrown when the server couldn't be deployed on the node.
        FileNotAvailableException
            Thrown when the file can't be read.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        pass

    @abstractmethod
    def openNodeStdErr(self, name: str, count: int, current: Current) -> FileIteratorPrx | None | Awaitable[FileIteratorPrx | None]:
        """
        Opens a node stderr file for reading.
        
        Parameters
        ----------
        name : str
            The node name.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        FileIteratorPrx | None | Awaitable[FileIteratorPrx | None]
            An iterator to read the file. This proxy is never null.
        
        Raises
        ------
        FileNotAvailableException
            Thrown when the file can't be read.
        NodeNotExistException
            Thrown when the node doesn't exist.
        NodeUnreachableException
            Thrown when the node is unreachable.
        """
        pass

    @abstractmethod
    def openNodeStdOut(self, name: str, count: int, current: Current) -> FileIteratorPrx | None | Awaitable[FileIteratorPrx | None]:
        """
        Opens a node stdout file for reading.
        
        Parameters
        ----------
        name : str
            The node name.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        FileIteratorPrx | None | Awaitable[FileIteratorPrx | None]
            An iterator to read the file. This proxy is never null.
        
        Raises
        ------
        FileNotAvailableException
            Thrown when the file can't be read.
        NodeNotExistException
            Thrown when the node doesn't exist.
        NodeUnreachableException
            Thrown when the node is unreachable.
        """
        pass

    @abstractmethod
    def openRegistryStdErr(self, name: str, count: int, current: Current) -> FileIteratorPrx | None | Awaitable[FileIteratorPrx | None]:
        """
        Opens a registry stderr file for reading.
        
        Parameters
        ----------
        name : str
            The registry name.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        FileIteratorPrx | None | Awaitable[FileIteratorPrx | None]
            An iterator to read the file. This proxy is never null.
        
        Raises
        ------
        FileNotAvailableException
            Thrown when the file can't be read.
        RegistryNotExistException
            Thrown when the registry doesn't exist.
        RegistryUnreachableException
            Thrown when the registry is unreachable.
        """
        pass

    @abstractmethod
    def openRegistryStdOut(self, name: str, count: int, current: Current) -> FileIteratorPrx | None | Awaitable[FileIteratorPrx | None]:
        """
        Opens a registry stdout file for reading.
        
        Parameters
        ----------
        name : str
            The registry name.
        count : int
            Specifies where to start reading the file. If negative, the file is read from the beginning.
            Otherwise, the file is read from the last ``count`` lines.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        FileIteratorPrx | None | Awaitable[FileIteratorPrx | None]
            An iterator to read the file. This proxy is never null.
        
        Raises
        ------
        FileNotAvailableException
            Thrown when the file can't be read.
        RegistryNotExistException
            Thrown when the registry doesn't exist.
        RegistryUnreachableException
            Thrown when the registry is unreachable.
        """
        pass

AdminSession._op_keepAlive = IcePy.Operation(
    "keepAlive",
    "keepAlive",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    None,
    ())
AdminSession._op_keepAlive.deprecate("As of Ice 3.8, there is no need to call this operation, and its implementation does nothing.")

AdminSession._op_getAdmin = IcePy.Operation(
    "getAdmin",
    "getAdmin",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), _IceGrid_AdminPrx_t, False, 0),
    ())

AdminSession._op_getAdminCallbackTemplate = IcePy.Operation(
    "getAdminCallbackTemplate",
    "getAdminCallbackTemplate",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), _Ice_ObjectPrx_t, False, 0),
    ())

AdminSession._op_setObservers = IcePy.Operation(
    "setObservers",
    "setObservers",
    OperationMode.Idempotent,
    None,
    (),
    (((), _IceGrid_RegistryObserverPrx_t, False, 0), ((), _IceGrid_NodeObserverPrx_t, False, 0), ((), _IceGrid_ApplicationObserverPrx_t, False, 0), ((), _IceGrid_AdapterObserverPrx_t, False, 0), ((), _IceGrid_ObjectObserverPrx_t, False, 0)),
    (),
    None,
    (_IceGrid_ObserverAlreadyRegisteredException_t,))

AdminSession._op_setObserversByIdentity = IcePy.Operation(
    "setObserversByIdentity",
    "setObserversByIdentity",
    OperationMode.Idempotent,
    None,
    (),
    (((), _Ice_Identity_t, False, 0), ((), _Ice_Identity_t, False, 0), ((), _Ice_Identity_t, False, 0), ((), _Ice_Identity_t, False, 0), ((), _Ice_Identity_t, False, 0)),
    (),
    None,
    (_IceGrid_ObserverAlreadyRegisteredException_t,))

AdminSession._op_startUpdate = IcePy.Operation(
    "startUpdate",
    "startUpdate",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    ((), IcePy._t_int, False, 0),
    (_IceGrid_AccessDeniedException_t,))

AdminSession._op_finishUpdate = IcePy.Operation(
    "finishUpdate",
    "finishUpdate",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    None,
    (_IceGrid_AccessDeniedException_t,))

AdminSession._op_getReplicaName = IcePy.Operation(
    "getReplicaName",
    "getReplicaName",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), IcePy._t_string, False, 0),
    ())

AdminSession._op_openServerLog = IcePy.Operation(
    "openServerLog",
    "openServerLog",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0), ((), IcePy._t_int, False, 0)),
    (),
    ((), _IceGrid_FileIteratorPrx_t, False, 0),
    (_IceGrid_FileNotAvailableException_t, _IceGrid_ServerNotExistException_t, _IceGrid_NodeUnreachableException_t, _IceGrid_DeploymentException_t))

AdminSession._op_openServerStdErr = IcePy.Operation(
    "openServerStdErr",
    "openServerStdErr",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), IcePy._t_int, False, 0)),
    (),
    ((), _IceGrid_FileIteratorPrx_t, False, 0),
    (_IceGrid_FileNotAvailableException_t, _IceGrid_ServerNotExistException_t, _IceGrid_NodeUnreachableException_t, _IceGrid_DeploymentException_t))

AdminSession._op_openServerStdOut = IcePy.Operation(
    "openServerStdOut",
    "openServerStdOut",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), IcePy._t_int, False, 0)),
    (),
    ((), _IceGrid_FileIteratorPrx_t, False, 0),
    (_IceGrid_FileNotAvailableException_t, _IceGrid_ServerNotExistException_t, _IceGrid_NodeUnreachableException_t, _IceGrid_DeploymentException_t))

AdminSession._op_openNodeStdErr = IcePy.Operation(
    "openNodeStdErr",
    "openNodeStdErr",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), IcePy._t_int, False, 0)),
    (),
    ((), _IceGrid_FileIteratorPrx_t, False, 0),
    (_IceGrid_FileNotAvailableException_t, _IceGrid_NodeNotExistException_t, _IceGrid_NodeUnreachableException_t))

AdminSession._op_openNodeStdOut = IcePy.Operation(
    "openNodeStdOut",
    "openNodeStdOut",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), IcePy._t_int, False, 0)),
    (),
    ((), _IceGrid_FileIteratorPrx_t, False, 0),
    (_IceGrid_FileNotAvailableException_t, _IceGrid_NodeNotExistException_t, _IceGrid_NodeUnreachableException_t))

AdminSession._op_openRegistryStdErr = IcePy.Operation(
    "openRegistryStdErr",
    "openRegistryStdErr",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), IcePy._t_int, False, 0)),
    (),
    ((), _IceGrid_FileIteratorPrx_t, False, 0),
    (_IceGrid_FileNotAvailableException_t, _IceGrid_RegistryNotExistException_t, _IceGrid_RegistryUnreachableException_t))

AdminSession._op_openRegistryStdOut = IcePy.Operation(
    "openRegistryStdOut",
    "openRegistryStdOut",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), IcePy._t_int, False, 0)),
    (),
    ((), _IceGrid_FileIteratorPrx_t, False, 0),
    (_IceGrid_FileNotAvailableException_t, _IceGrid_RegistryNotExistException_t, _IceGrid_RegistryUnreachableException_t))

__all__ = ["AdminSession", "AdminSessionPrx", "_IceGrid_AdminSessionPrx_t"]
