# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.Identity import _Ice_Identity_t

from Ice.Object import Object

from Ice.ObjectPrx import ObjectPrx
from Ice.ObjectPrx import checkedCast
from Ice.ObjectPrx import checkedCastAsync
from Ice.ObjectPrx import uncheckedCast

from Ice.ObjectPrx_forward import _Ice_ObjectPrx_t

from Ice.OperationMode import OperationMode

from Ice.StringSeq import _Ice_StringSeq_t

from IceGrid.AccessDeniedException import _IceGrid_AccessDeniedException_t

from IceGrid.AdapterInfoSeq import _IceGrid_AdapterInfoSeq_t

from IceGrid.AdapterNotExistException import _IceGrid_AdapterNotExistException_t

from IceGrid.Admin_forward import _IceGrid_AdminPrx_t

from IceGrid.ApplicationDescriptor import _IceGrid_ApplicationDescriptor_t

from IceGrid.ApplicationInfo import _IceGrid_ApplicationInfo_t

from IceGrid.ApplicationNotExistException import _IceGrid_ApplicationNotExistException_t

from IceGrid.ApplicationUpdateDescriptor import _IceGrid_ApplicationUpdateDescriptor_t

from IceGrid.BadSignalException import _IceGrid_BadSignalException_t

from IceGrid.DeploymentException import _IceGrid_DeploymentException_t

from IceGrid.LoadInfo import _IceGrid_LoadInfo_t

from IceGrid.NodeInfo import _IceGrid_NodeInfo_t

from IceGrid.NodeNotExistException import _IceGrid_NodeNotExistException_t

from IceGrid.NodeUnreachableException import _IceGrid_NodeUnreachableException_t

from IceGrid.ObjectExistsException import _IceGrid_ObjectExistsException_t

from IceGrid.ObjectInfo import _IceGrid_ObjectInfo_t

from IceGrid.ObjectInfoSeq import _IceGrid_ObjectInfoSeq_t

from IceGrid.ObjectNotRegisteredException import _IceGrid_ObjectNotRegisteredException_t

from IceGrid.RegistryInfo import _IceGrid_RegistryInfo_t

from IceGrid.RegistryNotExistException import _IceGrid_RegistryNotExistException_t

from IceGrid.RegistryUnreachableException import _IceGrid_RegistryUnreachableException_t

from IceGrid.ServerInfo import _IceGrid_ServerInfo_t

from IceGrid.ServerInstanceDescriptor import _IceGrid_ServerInstanceDescriptor_t

from IceGrid.ServerNotExistException import _IceGrid_ServerNotExistException_t

from IceGrid.ServerStartException import _IceGrid_ServerStartException_t

from IceGrid.ServerState import _IceGrid_ServerState_t

from IceGrid.ServerStopException import _IceGrid_ServerStopException_t

from abc import ABC
from abc import abstractmethod

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from Ice.Current import Current
    from Ice.Identity import Identity
    from IceGrid.AdapterInfo import AdapterInfo
    from IceGrid.ApplicationDescriptor import ApplicationDescriptor
    from IceGrid.ApplicationInfo import ApplicationInfo
    from IceGrid.ApplicationUpdateDescriptor import ApplicationUpdateDescriptor
    from IceGrid.LoadInfo import LoadInfo
    from IceGrid.NodeInfo import NodeInfo
    from IceGrid.ObjectInfo import ObjectInfo
    from IceGrid.RegistryInfo import RegistryInfo
    from IceGrid.ServerInfo import ServerInfo
    from IceGrid.ServerInstanceDescriptor import ServerInstanceDescriptor
    from IceGrid.ServerState import ServerState
    from collections.abc import Awaitable
    from collections.abc import Sequence


class AdminPrx(ObjectPrx):
    """
    Provides administrative access to an IceGrid deployment.
    
    Notes
    -----
        The Slice compiler generated this proxy class from Slice interface ``::IceGrid::Admin``.
    """

    def addApplication(self, descriptor: ApplicationDescriptor, context: dict[str, str] | None = None) -> None:
        """
        Adds an application to IceGrid.
        
        Parameters
        ----------
        descriptor : ApplicationDescriptor
            The application descriptor.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        AccessDeniedException
            Thrown when the session doesn't hold the exclusive lock or when another
            session is holding the lock.
        DeploymentException
            Thrown when the application deployment failed.
        """
        return Admin._op_addApplication.invoke(self, ((descriptor, ), context))

    def addApplicationAsync(self, descriptor: ApplicationDescriptor, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Adds an application to IceGrid.
        
        Parameters
        ----------
        descriptor : ApplicationDescriptor
            The application descriptor.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_addApplication.invokeAsync(self, ((descriptor, ), context))

    def syncApplication(self, descriptor: ApplicationDescriptor, context: dict[str, str] | None = None) -> None:
        """
        Synchronizes a deployed application. This operation replaces the current descriptor with a new descriptor.
        
        Parameters
        ----------
        descriptor : ApplicationDescriptor
            The new application descriptor.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        AccessDeniedException
            Thrown when the session doesn't hold the exclusive lock or when another
            session is holding the lock.
        ApplicationNotExistException
            Thrown when the application doesn't exist.
        DeploymentException
            Thrown when the application deployment failed.
        """
        return Admin._op_syncApplication.invoke(self, ((descriptor, ), context))

    def syncApplicationAsync(self, descriptor: ApplicationDescriptor, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Synchronizes a deployed application. This operation replaces the current descriptor with a new descriptor.
        
        Parameters
        ----------
        descriptor : ApplicationDescriptor
            The new application descriptor.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_syncApplication.invokeAsync(self, ((descriptor, ), context))

    def updateApplication(self, descriptor: ApplicationUpdateDescriptor, context: dict[str, str] | None = None) -> None:
        """
        Updates a deployed application.
        
        Parameters
        ----------
        descriptor : ApplicationUpdateDescriptor
            The update descriptor.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        AccessDeniedException
            Thrown when the session doesn't hold the exclusive lock or when another
            session is holding the lock.
        ApplicationNotExistException
            Thrown when the application doesn't exist.
        DeploymentException
            Thrown when the application deployment failed.
        """
        return Admin._op_updateApplication.invoke(self, ((descriptor, ), context))

    def updateApplicationAsync(self, descriptor: ApplicationUpdateDescriptor, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Updates a deployed application.
        
        Parameters
        ----------
        descriptor : ApplicationUpdateDescriptor
            The update descriptor.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_updateApplication.invokeAsync(self, ((descriptor, ), context))

    def syncApplicationWithoutRestart(self, descriptor: ApplicationDescriptor, context: dict[str, str] | None = None) -> None:
        """
        Synchronizes a deployed application. This operation replaces the current descriptor with a new descriptor
        only if no server restarts are necessary for the update of the application. If some servers need to be
        restarted, the synchronization is rejected with a DeploymentException.
        
        Parameters
        ----------
        descriptor : ApplicationDescriptor
            The application descriptor.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        AccessDeniedException
            Thrown when the session doesn't hold the exclusive lock or when another
            session is holding the lock.
        ApplicationNotExistException
            Thrown when the application doesn't exist.
        DeploymentException
            Thrown when the application deployment failed.
        """
        return Admin._op_syncApplicationWithoutRestart.invoke(self, ((descriptor, ), context))

    def syncApplicationWithoutRestartAsync(self, descriptor: ApplicationDescriptor, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Synchronizes a deployed application. This operation replaces the current descriptor with a new descriptor
        only if no server restarts are necessary for the update of the application. If some servers need to be
        restarted, the synchronization is rejected with a DeploymentException.
        
        Parameters
        ----------
        descriptor : ApplicationDescriptor
            The application descriptor.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_syncApplicationWithoutRestart.invokeAsync(self, ((descriptor, ), context))

    def updateApplicationWithoutRestart(self, descriptor: ApplicationUpdateDescriptor, context: dict[str, str] | None = None) -> None:
        """
        Updates a deployed application. This operation succeeds only when no server restarts are necessary for the
        update of the application. If some servers need to be restarted, the synchronization is rejected with a
        DeploymentException.
        
        Parameters
        ----------
        descriptor : ApplicationUpdateDescriptor
            The update descriptor.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        AccessDeniedException
            Thrown when the session doesn't hold the exclusive lock or when another
            session is holding the lock.
        ApplicationNotExistException
            Thrown when the application doesn't exist.
        DeploymentException
            Thrown when the application deployment failed.
        """
        return Admin._op_updateApplicationWithoutRestart.invoke(self, ((descriptor, ), context))

    def updateApplicationWithoutRestartAsync(self, descriptor: ApplicationUpdateDescriptor, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Updates a deployed application. This operation succeeds only when no server restarts are necessary for the
        update of the application. If some servers need to be restarted, the synchronization is rejected with a
        DeploymentException.
        
        Parameters
        ----------
        descriptor : ApplicationUpdateDescriptor
            The update descriptor.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_updateApplicationWithoutRestart.invokeAsync(self, ((descriptor, ), context))

    def removeApplication(self, name: str, context: dict[str, str] | None = None) -> None:
        """
        Removes an application from IceGrid.
        
        Parameters
        ----------
        name : str
            The application name.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        AccessDeniedException
            Thrown when the session doesn't hold the exclusive lock or when another
            session is holding the lock.
        ApplicationNotExistException
            Thrown when the application doesn't exist.
        DeploymentException
            Thrown when the application deployment failed.
        """
        return Admin._op_removeApplication.invoke(self, ((name, ), context))

    def removeApplicationAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Removes an application from IceGrid.
        
        Parameters
        ----------
        name : str
            The application name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_removeApplication.invokeAsync(self, ((name, ), context))

    def instantiateServer(self, application: str, node: str, desc: ServerInstanceDescriptor, context: dict[str, str] | None = None) -> None:
        """
        Instantiates a server template.
        
        Parameters
        ----------
        application : str
            The application name.
        node : str
            The name of the node where the server will be deployed.
        desc : ServerInstanceDescriptor
            The descriptor of the server instance to deploy.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        AccessDeniedException
            Thrown when the session doesn't hold the exclusive lock or when another
            session is holding the lock.
        ApplicationNotExistException
            Thrown when the application doesn't exist.
        DeploymentException
            Thrown when the application deployment failed.
        """
        return Admin._op_instantiateServer.invoke(self, ((application, node, desc), context))

    def instantiateServerAsync(self, application: str, node: str, desc: ServerInstanceDescriptor, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Instantiates a server template.
        
        Parameters
        ----------
        application : str
            The application name.
        node : str
            The name of the node where the server will be deployed.
        desc : ServerInstanceDescriptor
            The descriptor of the server instance to deploy.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_instantiateServer.invokeAsync(self, ((application, node, desc), context))

    def getApplicationInfo(self, name: str, context: dict[str, str] | None = None) -> ApplicationInfo:
        """
        Gets an application descriptor.
        
        Parameters
        ----------
        name : str
            The application name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ApplicationInfo
            The application descriptor.
        
        Raises
        ------
        ApplicationNotExistException
            Thrown when the application doesn't exist.
        """
        return Admin._op_getApplicationInfo.invoke(self, ((name, ), context))

    def getApplicationInfoAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[ApplicationInfo]:
        """
        Gets an application descriptor.
        
        Parameters
        ----------
        name : str
            The application name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ApplicationInfo]
            The application descriptor.
        """
        return Admin._op_getApplicationInfo.invokeAsync(self, ((name, ), context))

    def getDefaultApplicationDescriptor(self, context: dict[str, str] | None = None) -> ApplicationDescriptor:
        """
        Gets the default application descriptor.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ApplicationDescriptor
            The default application descriptor.
        
        Raises
        ------
        DeploymentException
            Thrown when the default application descriptor is invalid or unreachable.
        """
        return Admin._op_getDefaultApplicationDescriptor.invoke(self, ((), context))

    def getDefaultApplicationDescriptorAsync(self, context: dict[str, str] | None = None) -> Awaitable[ApplicationDescriptor]:
        """
        Gets the default application descriptor.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ApplicationDescriptor]
            The default application descriptor.
        """
        return Admin._op_getDefaultApplicationDescriptor.invokeAsync(self, ((), context))

    def getAllApplicationNames(self, context: dict[str, str] | None = None) -> list[str]:
        """
        Gets all the IceGrid applications currently registered.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        list[str]
            The application names.
        """
        return Admin._op_getAllApplicationNames.invoke(self, ((), context))

    def getAllApplicationNamesAsync(self, context: dict[str, str] | None = None) -> Awaitable[list[str]]:
        """
        Gets all the IceGrid applications currently registered.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[list[str]]
            The application names.
        """
        return Admin._op_getAllApplicationNames.invokeAsync(self, ((), context))

    def getServerInfo(self, id: str, context: dict[str, str] | None = None) -> ServerInfo:
        """
        Gets information about a server.
        
        Parameters
        ----------
        id : str
            The server ID.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ServerInfo
            The server information.
        
        Raises
        ------
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        return Admin._op_getServerInfo.invoke(self, ((id, ), context))

    def getServerInfoAsync(self, id: str, context: dict[str, str] | None = None) -> Awaitable[ServerInfo]:
        """
        Gets information about a server.
        
        Parameters
        ----------
        id : str
            The server ID.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ServerInfo]
            The server information.
        """
        return Admin._op_getServerInfo.invokeAsync(self, ((id, ), context))

    def getServerState(self, id: str, context: dict[str, str] | None = None) -> ServerState:
        """
        Gets the state of a server.
        
        Parameters
        ----------
        id : str
            The server ID.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ServerState
            The server state.
        
        Raises
        ------
        DeploymentException
            Thrown when the deployment of the server failed.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        return Admin._op_getServerState.invoke(self, ((id, ), context))

    def getServerStateAsync(self, id: str, context: dict[str, str] | None = None) -> Awaitable[ServerState]:
        """
        Gets the state of a server.
        
        Parameters
        ----------
        id : str
            The server ID.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ServerState]
            The server state.
        """
        return Admin._op_getServerState.invokeAsync(self, ((id, ), context))

    def getServerPid(self, id: str, context: dict[str, str] | None = None) -> int:
        """
        Gets the system process ID of a server. The process ID is operating system dependent.
        
        Parameters
        ----------
        id : str
            The server ID.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        int
            The process ID.
        
        Raises
        ------
        DeploymentException
            Thrown when the deployment of the server failed.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        return Admin._op_getServerPid.invoke(self, ((id, ), context))

    def getServerPidAsync(self, id: str, context: dict[str, str] | None = None) -> Awaitable[int]:
        """
        Gets the system process ID of a server. The process ID is operating system dependent.
        
        Parameters
        ----------
        id : str
            The server ID.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[int]
            The process ID.
        """
        return Admin._op_getServerPid.invokeAsync(self, ((id, ), context))

    def getServerAdminCategory(self, context: dict[str, str] | None = None) -> str:
        """
        Gets the category for server admin objects. You can manufacture a server admin proxy from the admin proxy by
        changing its identity: use the server ID as name and the returned category as category.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        str
            The category for server admin objects.
        """
        return Admin._op_getServerAdminCategory.invoke(self, ((), context))

    def getServerAdminCategoryAsync(self, context: dict[str, str] | None = None) -> Awaitable[str]:
        """
        Gets the category for server admin objects. You can manufacture a server admin proxy from the admin proxy by
        changing its identity: use the server ID as name and the returned category as category.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[str]
            The category for server admin objects.
        """
        return Admin._op_getServerAdminCategory.invokeAsync(self, ((), context))

    def getServerAdmin(self, id: str, context: dict[str, str] | None = None) -> ObjectPrx | None:
        """
        Gets a proxy to the admin object of a server.
        
        Parameters
        ----------
        id : str
            The server ID.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ObjectPrx | None
            A proxy to the admin object of the server. This proxy is never null.
        
        Raises
        ------
        DeploymentException
            Thrown when the deployment of the server failed.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        return Admin._op_getServerAdmin.invoke(self, ((id, ), context))

    def getServerAdminAsync(self, id: str, context: dict[str, str] | None = None) -> Awaitable[ObjectPrx | None]:
        """
        Gets a proxy to the admin object of a server.
        
        Parameters
        ----------
        id : str
            The server ID.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ObjectPrx | None]
            A proxy to the admin object of the server. This proxy is never null.
        """
        return Admin._op_getServerAdmin.invokeAsync(self, ((id, ), context))

    def enableServer(self, id: str, enabled: bool, context: dict[str, str] | None = None) -> None:
        """
        Enables or disables a server. A disabled server can't be started on demand or administratively. The enable
        state of the server is not persistent: if the node is shut down and restarted, the server will be enabled by
        default.
        
        Parameters
        ----------
        id : str
            The server ID.
        enabled : bool
            ``true`` to enable the server, ``false`` to disable it.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        DeploymentException
            Thrown when the deployment of the server failed.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        return Admin._op_enableServer.invoke(self, ((id, enabled), context))

    def enableServerAsync(self, id: str, enabled: bool, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Enables or disables a server. A disabled server can't be started on demand or administratively. The enable
        state of the server is not persistent: if the node is shut down and restarted, the server will be enabled by
        default.
        
        Parameters
        ----------
        id : str
            The server ID.
        enabled : bool
            ``true`` to enable the server, ``false`` to disable it.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_enableServer.invokeAsync(self, ((id, enabled), context))

    def isServerEnabled(self, id: str, context: dict[str, str] | None = None) -> bool:
        """
        Checks if the server is enabled or disabled.
        
        Parameters
        ----------
        id : str
            The server ID.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        bool
            ``true`` if the server is enabled, ``false`` otherwise.
        
        Raises
        ------
        DeploymentException
            Thrown when the deployment of the server failed.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        return Admin._op_isServerEnabled.invoke(self, ((id, ), context))

    def isServerEnabledAsync(self, id: str, context: dict[str, str] | None = None) -> Awaitable[bool]:
        """
        Checks if the server is enabled or disabled.
        
        Parameters
        ----------
        id : str
            The server ID.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[bool]
            ``true`` if the server is enabled, ``false`` otherwise.
        """
        return Admin._op_isServerEnabled.invokeAsync(self, ((id, ), context))

    def startServer(self, id: str, context: dict[str, str] | None = None) -> None:
        """
        Starts a server and waits for its activation.
        
        Parameters
        ----------
        id : str
            The server id.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        DeploymentException
            Thrown when the deployment of the server failed.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        ServerStartException
            Thrown when the server startup failed.
        """
        return Admin._op_startServer.invoke(self, ((id, ), context))

    def startServerAsync(self, id: str, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Starts a server and waits for its activation.
        
        Parameters
        ----------
        id : str
            The server id.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_startServer.invokeAsync(self, ((id, ), context))

    def stopServer(self, id: str, context: dict[str, str] | None = None) -> None:
        """
        Stops a server.
        
        Parameters
        ----------
        id : str
            The server ID.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        DeploymentException
            Thrown when the deployment of the server failed.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        ServerStopException
            Thrown when the server stop failed.
        """
        return Admin._op_stopServer.invoke(self, ((id, ), context))

    def stopServerAsync(self, id: str, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Stops a server.
        
        Parameters
        ----------
        id : str
            The server ID.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_stopServer.invokeAsync(self, ((id, ), context))

    def sendSignal(self, id: str, signal: str, context: dict[str, str] | None = None) -> None:
        """
        Sends a signal to a server.
        
        Parameters
        ----------
        id : str
            The server ID.
        signal : str
            The signal, for example SIGTERM or 15.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        BadSignalException
            Thrown when the signal is not recognized by the target server.
        DeploymentException
            Thrown when the deployment of the server failed.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        return Admin._op_sendSignal.invoke(self, ((id, signal), context))

    def sendSignalAsync(self, id: str, signal: str, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Sends a signal to a server.
        
        Parameters
        ----------
        id : str
            The server ID.
        signal : str
            The signal, for example SIGTERM or 15.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_sendSignal.invokeAsync(self, ((id, signal), context))

    def getAllServerIds(self, context: dict[str, str] | None = None) -> list[str]:
        """
        Gets the IDs of all the servers registered with IceGrid.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        list[str]
            The server IDs.
        """
        return Admin._op_getAllServerIds.invoke(self, ((), context))

    def getAllServerIdsAsync(self, context: dict[str, str] | None = None) -> Awaitable[list[str]]:
        """
        Gets the IDs of all the servers registered with IceGrid.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[list[str]]
            The server IDs.
        """
        return Admin._op_getAllServerIds.invokeAsync(self, ((), context))

    def getAdapterInfo(self, id: str, context: dict[str, str] | None = None) -> list[AdapterInfo]:
        """
        Gets adapter information for the replica group or adapter with the given ID.
        
        Parameters
        ----------
        id : str
            The adapter or replica group ID.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        list[AdapterInfo]
            A sequence of AdapterInfo. If ``id`` refers to an adapter, this sequence contains a single element.
            If ``id`` refers to a replica group, this sequence contains adapter information for each member of the
            replica group.
        
        Raises
        ------
        AdapterNotExistException
            Thrown when the adapter or replica group doesn't exist.
        """
        return Admin._op_getAdapterInfo.invoke(self, ((id, ), context))

    def getAdapterInfoAsync(self, id: str, context: dict[str, str] | None = None) -> Awaitable[list[AdapterInfo]]:
        """
        Gets adapter information for the replica group or adapter with the given ID.
        
        Parameters
        ----------
        id : str
            The adapter or replica group ID.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[list[AdapterInfo]]
            A sequence of AdapterInfo. If ``id`` refers to an adapter, this sequence contains a single element.
            If ``id`` refers to a replica group, this sequence contains adapter information for each member of the
            replica group.
        """
        return Admin._op_getAdapterInfo.invokeAsync(self, ((id, ), context))

    def removeAdapter(self, id: str, context: dict[str, str] | None = None) -> None:
        """
        Removes the adapter with the given ID.
        
        Parameters
        ----------
        id : str
            The adapter ID.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        AdapterNotExistException
            Thrown when the adapter doesn't exist.
        DeploymentException
            Thrown when the application deployment failed.
        """
        return Admin._op_removeAdapter.invoke(self, ((id, ), context))

    def removeAdapterAsync(self, id: str, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Removes the adapter with the given ID.
        
        Parameters
        ----------
        id : str
            The adapter ID.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_removeAdapter.invokeAsync(self, ((id, ), context))

    def getAllAdapterIds(self, context: dict[str, str] | None = None) -> list[str]:
        """
        Gets the IDs of all adapters registered with IceGrid.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        list[str]
            The adapter IDs.
        """
        return Admin._op_getAllAdapterIds.invoke(self, ((), context))

    def getAllAdapterIdsAsync(self, context: dict[str, str] | None = None) -> Awaitable[list[str]]:
        """
        Gets the IDs of all adapters registered with IceGrid.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[list[str]]
            The adapter IDs.
        """
        return Admin._op_getAllAdapterIds.invokeAsync(self, ((), context))

    def addObject(self, obj: ObjectPrx | None, context: dict[str, str] | None = None) -> None:
        """
        Adds an object to the object registry. IceGrid gets the object type by calling ``ice_id`` on ``obj``. The
        object must be reachable.
        
        Parameters
        ----------
        obj : ObjectPrx | None
            A proxy to the object. This proxy is never null.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        DeploymentException
            Thrown when the object can't be added.
        ObjectExistsException
            Thrown when the object is already registered.
        """
        return Admin._op_addObject.invoke(self, ((obj, ), context))

    def addObjectAsync(self, obj: ObjectPrx | None, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Adds an object to the object registry. IceGrid gets the object type by calling ``ice_id`` on ``obj``. The
        object must be reachable.
        
        Parameters
        ----------
        obj : ObjectPrx | None
            A proxy to the object. This proxy is never null.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_addObject.invokeAsync(self, ((obj, ), context))

    def updateObject(self, obj: ObjectPrx | None, context: dict[str, str] | None = None) -> None:
        """
        Updates an object in the object registry. Only objects added with this interface can be updated with this
        operation. Objects added with deployment descriptors should be updated with the deployment mechanism.
        
        Parameters
        ----------
        obj : ObjectPrx | None
            A proxy to the object. This proxy is never null.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        DeploymentException
            Thrown when the object can't be updated.
        ObjectNotRegisteredException
            Thrown when the object isn't registered with the registry.
        """
        return Admin._op_updateObject.invoke(self, ((obj, ), context))

    def updateObjectAsync(self, obj: ObjectPrx | None, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Updates an object in the object registry. Only objects added with this interface can be updated with this
        operation. Objects added with deployment descriptors should be updated with the deployment mechanism.
        
        Parameters
        ----------
        obj : ObjectPrx | None
            A proxy to the object. This proxy is never null.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_updateObject.invokeAsync(self, ((obj, ), context))

    def addObjectWithType(self, obj: ObjectPrx | None, type: str, context: dict[str, str] | None = None) -> None:
        """
        Adds an object to the object registry and explicitly specifies its type.
        
        Parameters
        ----------
        obj : ObjectPrx | None
            The object to be added to the registry. The proxy is never null.
        type : str
            The type name.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        DeploymentException
            Thrown when the application deployment failed.
        ObjectExistsException
            Thrown when the object is already registered.
        """
        return Admin._op_addObjectWithType.invoke(self, ((obj, type), context))

    def addObjectWithTypeAsync(self, obj: ObjectPrx | None, type: str, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Adds an object to the object registry and explicitly specifies its type.
        
        Parameters
        ----------
        obj : ObjectPrx | None
            The object to be added to the registry. The proxy is never null.
        type : str
            The type name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_addObjectWithType.invokeAsync(self, ((obj, type), context))

    def removeObject(self, id: Identity, context: dict[str, str] | None = None) -> None:
        """
        Removes an object from the object registry. Only objects added with this interface can be removed with this
        operation. Objects added with deployment descriptors should be removed with the deployment mechanism.
        
        Parameters
        ----------
        id : Identity
            The identity of the object to remove.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        DeploymentException
            Thrown when the object can't be removed.
        ObjectNotRegisteredException
            Thrown when the object isn't registered with the registry.
        """
        return Admin._op_removeObject.invoke(self, ((id, ), context))

    def removeObjectAsync(self, id: Identity, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Removes an object from the object registry. Only objects added with this interface can be removed with this
        operation. Objects added with deployment descriptors should be removed with the deployment mechanism.
        
        Parameters
        ----------
        id : Identity
            The identity of the object to remove.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_removeObject.invokeAsync(self, ((id, ), context))

    def getObjectInfo(self, id: Identity, context: dict[str, str] | None = None) -> ObjectInfo:
        """
        Gets the object info for the object.
        
        Parameters
        ----------
        id : Identity
            The identity of the object.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ObjectInfo
            The object info.
        
        Raises
        ------
        ObjectNotRegisteredException
            Thrown when the object isn't registered with the registry.
        """
        return Admin._op_getObjectInfo.invoke(self, ((id, ), context))

    def getObjectInfoAsync(self, id: Identity, context: dict[str, str] | None = None) -> Awaitable[ObjectInfo]:
        """
        Gets the object info for the object.
        
        Parameters
        ----------
        id : Identity
            The identity of the object.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ObjectInfo]
            The object info.
        """
        return Admin._op_getObjectInfo.invokeAsync(self, ((id, ), context))

    def getObjectInfosByType(self, type: str, context: dict[str, str] | None = None) -> list[ObjectInfo]:
        """
        Gets the object info of all the registered objects with a given type.
        
        Parameters
        ----------
        type : str
            The type name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        list[ObjectInfo]
            The object infos.
        """
        return Admin._op_getObjectInfosByType.invoke(self, ((type, ), context))

    def getObjectInfosByTypeAsync(self, type: str, context: dict[str, str] | None = None) -> Awaitable[list[ObjectInfo]]:
        """
        Gets the object info of all the registered objects with a given type.
        
        Parameters
        ----------
        type : str
            The type name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[list[ObjectInfo]]
            The object infos.
        """
        return Admin._op_getObjectInfosByType.invokeAsync(self, ((type, ), context))

    def getAllObjectInfos(self, expr: str, context: dict[str, str] | None = None) -> list[ObjectInfo]:
        """
        Gets the object info of all the registered objects whose stringified identities match the given expression.
        
        Parameters
        ----------
        expr : str
            The expression to match against the stringified identities of registered objects. The expression
            may contain a trailing wildcard (``*``) character.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        list[ObjectInfo]
            All the object infos with a stringified identity matching the given expression.
        """
        return Admin._op_getAllObjectInfos.invoke(self, ((expr, ), context))

    def getAllObjectInfosAsync(self, expr: str, context: dict[str, str] | None = None) -> Awaitable[list[ObjectInfo]]:
        """
        Gets the object info of all the registered objects whose stringified identities match the given expression.
        
        Parameters
        ----------
        expr : str
            The expression to match against the stringified identities of registered objects. The expression
            may contain a trailing wildcard (``*``) character.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[list[ObjectInfo]]
            All the object infos with a stringified identity matching the given expression.
        """
        return Admin._op_getAllObjectInfos.invokeAsync(self, ((expr, ), context))

    def pingNode(self, name: str, context: dict[str, str] | None = None) -> bool:
        """
        Pings an IceGrid node to see if it is active.
        
        Parameters
        ----------
        name : str
            The node name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        bool
            ``true`` if the node ping succeeded, ``false`` otherwise.
        
        Raises
        ------
        NodeNotExistException
            Thrown when the node doesn't exist.
        """
        return Admin._op_pingNode.invoke(self, ((name, ), context))

    def pingNodeAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[bool]:
        """
        Pings an IceGrid node to see if it is active.
        
        Parameters
        ----------
        name : str
            The node name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[bool]
            ``true`` if the node ping succeeded, ``false`` otherwise.
        """
        return Admin._op_pingNode.invokeAsync(self, ((name, ), context))

    def getNodeLoad(self, name: str, context: dict[str, str] | None = None) -> LoadInfo:
        """
        Gets the load averages of a node.
        
        Parameters
        ----------
        name : str
            The node name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        LoadInfo
            The node load information.
        
        Raises
        ------
        NodeNotExistException
            Thrown when the node doesn't exist.
        NodeUnreachableException
            Thrown when the node is unreachable.
        """
        return Admin._op_getNodeLoad.invoke(self, ((name, ), context))

    def getNodeLoadAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[LoadInfo]:
        """
        Gets the load averages of a node.
        
        Parameters
        ----------
        name : str
            The node name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[LoadInfo]
            The node load information.
        """
        return Admin._op_getNodeLoad.invokeAsync(self, ((name, ), context))

    def getNodeInfo(self, name: str, context: dict[str, str] | None = None) -> NodeInfo:
        """
        Gets the node information of a node.
        
        Parameters
        ----------
        name : str
            The node name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        NodeInfo
            The node information.
        
        Raises
        ------
        NodeNotExistException
            Thrown when the node doesn't exist.
        NodeUnreachableException
            Thrown when the node is unreachable.
        """
        return Admin._op_getNodeInfo.invoke(self, ((name, ), context))

    def getNodeInfoAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[NodeInfo]:
        """
        Gets the node information of a node.
        
        Parameters
        ----------
        name : str
            The node name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[NodeInfo]
            The node information.
        """
        return Admin._op_getNodeInfo.invokeAsync(self, ((name, ), context))

    def getNodeAdmin(self, name: str, context: dict[str, str] | None = None) -> ObjectPrx | None:
        """
        Gets a proxy to the admin object of an IceGrid node.
        
        Parameters
        ----------
        name : str
            The IceGrid node name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ObjectPrx | None
            A proxy to the IceGrid node's admin object. This proxy is never null.
        
        Raises
        ------
        NodeNotExistException
            Thrown when the node doesn't exist.
        NodeUnreachableException
            Thrown when the node is unreachable.
        """
        return Admin._op_getNodeAdmin.invoke(self, ((name, ), context))

    def getNodeAdminAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[ObjectPrx | None]:
        """
        Gets a proxy to the admin object of an IceGrid node.
        
        Parameters
        ----------
        name : str
            The IceGrid node name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ObjectPrx | None]
            A proxy to the IceGrid node's admin object. This proxy is never null.
        """
        return Admin._op_getNodeAdmin.invokeAsync(self, ((name, ), context))

    def getNodeProcessorSocketCount(self, name: str, context: dict[str, str] | None = None) -> int:
        """
        Gets the number of physical processor sockets in the computer where an IceGrid node is deployed.
        Note that this operation returns 1 on operating systems where this can't be automatically determined and
        where the ``IceGrid.Node.ProcessorSocketCount`` property for the node is not set.
        
        Parameters
        ----------
        name : str
            The node name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        int
            The number of processor sockets or 1 if the number of sockets can't be determined.
        
        Raises
        ------
        NodeNotExistException
            Thrown when the node doesn't exist.
        NodeUnreachableException
            Thrown when the node is unreachable.
        """
        return Admin._op_getNodeProcessorSocketCount.invoke(self, ((name, ), context))

    def getNodeProcessorSocketCountAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[int]:
        """
        Gets the number of physical processor sockets in the computer where an IceGrid node is deployed.
        Note that this operation returns 1 on operating systems where this can't be automatically determined and
        where the ``IceGrid.Node.ProcessorSocketCount`` property for the node is not set.
        
        Parameters
        ----------
        name : str
            The node name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[int]
            The number of processor sockets or 1 if the number of sockets can't be determined.
        """
        return Admin._op_getNodeProcessorSocketCount.invokeAsync(self, ((name, ), context))

    def shutdownNode(self, name: str, context: dict[str, str] | None = None) -> None:
        """
        Shuts down an IceGrid node.
        
        Parameters
        ----------
        name : str
            The node name.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        NodeNotExistException
            Thrown when the node doesn't exist.
        NodeUnreachableException
            Thrown when the node is unreachable.
        """
        return Admin._op_shutdownNode.invoke(self, ((name, ), context))

    def shutdownNodeAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Shuts down an IceGrid node.
        
        Parameters
        ----------
        name : str
            The node name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_shutdownNode.invokeAsync(self, ((name, ), context))

    def getNodeHostname(self, name: str, context: dict[str, str] | None = None) -> str:
        """
        Get the hostname of a node.
        
        Parameters
        ----------
        name : str
            The node name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        str
            The node hostname.
        
        Raises
        ------
        NodeNotExistException
            Thrown when the node doesn't exist.
        NodeUnreachableException
            Thrown when the node is unreachable.
        """
        return Admin._op_getNodeHostname.invoke(self, ((name, ), context))

    def getNodeHostnameAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[str]:
        """
        Get the hostname of a node.
        
        Parameters
        ----------
        name : str
            The node name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[str]
            The node hostname.
        """
        return Admin._op_getNodeHostname.invokeAsync(self, ((name, ), context))

    def getAllNodeNames(self, context: dict[str, str] | None = None) -> list[str]:
        """
        Gets the names of all IceGrid nodes currently registered.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        list[str]
            The node names.
        """
        return Admin._op_getAllNodeNames.invoke(self, ((), context))

    def getAllNodeNamesAsync(self, context: dict[str, str] | None = None) -> Awaitable[list[str]]:
        """
        Gets the names of all IceGrid nodes currently registered.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[list[str]]
            The node names.
        """
        return Admin._op_getAllNodeNames.invokeAsync(self, ((), context))

    def pingRegistry(self, name: str, context: dict[str, str] | None = None) -> bool:
        """
        Pings an IceGrid registry to see if it is active.
        
        Parameters
        ----------
        name : str
            The registry name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        bool
            ``true`` if the registry ping succeeded, ``false`` otherwise.
        
        Raises
        ------
        RegistryNotExistException
            Thrown when the registry doesn't exist.
        """
        return Admin._op_pingRegistry.invoke(self, ((name, ), context))

    def pingRegistryAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[bool]:
        """
        Pings an IceGrid registry to see if it is active.
        
        Parameters
        ----------
        name : str
            The registry name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[bool]
            ``true`` if the registry ping succeeded, ``false`` otherwise.
        """
        return Admin._op_pingRegistry.invokeAsync(self, ((name, ), context))

    def getRegistryInfo(self, name: str, context: dict[str, str] | None = None) -> RegistryInfo:
        """
        Gets the registry information of an IceGrid registry.
        
        Parameters
        ----------
        name : str
            The registry name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        RegistryInfo
            The registry information.
        
        Raises
        ------
        RegistryNotExistException
            Thrown when the registry doesn't exist.
        RegistryUnreachableException
            Thrown when the registry is unreachable.
        """
        return Admin._op_getRegistryInfo.invoke(self, ((name, ), context))

    def getRegistryInfoAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[RegistryInfo]:
        """
        Gets the registry information of an IceGrid registry.
        
        Parameters
        ----------
        name : str
            The registry name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[RegistryInfo]
            The registry information.
        """
        return Admin._op_getRegistryInfo.invokeAsync(self, ((name, ), context))

    def getRegistryAdmin(self, name: str, context: dict[str, str] | None = None) -> ObjectPrx | None:
        """
        Gets a proxy to the admin object of an IceGrid registry.
        
        Parameters
        ----------
        name : str
            The registry name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        ObjectPrx | None
            A proxy to the admin object of an IceGrid registry. This proxy is never null.
        
        Raises
        ------
        RegistryNotExistException
            Thrown when the registry doesn't exist.
        """
        return Admin._op_getRegistryAdmin.invoke(self, ((name, ), context))

    def getRegistryAdminAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[ObjectPrx | None]:
        """
        Gets a proxy to the admin object of an IceGrid registry.
        
        Parameters
        ----------
        name : str
            The registry name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[ObjectPrx | None]
            A proxy to the admin object of an IceGrid registry. This proxy is never null.
        """
        return Admin._op_getRegistryAdmin.invokeAsync(self, ((name, ), context))

    def shutdownRegistry(self, name: str, context: dict[str, str] | None = None) -> None:
        """
        Shuts down an IceGrid registry.
        
        Parameters
        ----------
        name : str
            The registry name.
        context : dict[str, str]
            The request context for the invocation.
        
        Raises
        ------
        RegistryNotExistException
            Thrown when the registry doesn't exist.
        RegistryUnreachableException
            Thrown when the registry is unreachable.
        """
        return Admin._op_shutdownRegistry.invoke(self, ((name, ), context))

    def shutdownRegistryAsync(self, name: str, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Shuts down an IceGrid registry.
        
        Parameters
        ----------
        name : str
            The registry name.
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_shutdownRegistry.invokeAsync(self, ((name, ), context))

    def getAllRegistryNames(self, context: dict[str, str] | None = None) -> list[str]:
        """
        Gets the names of all the IceGrid registries currently registered.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        list[str]
            The registry names.
        """
        return Admin._op_getAllRegistryNames.invoke(self, ((), context))

    def getAllRegistryNamesAsync(self, context: dict[str, str] | None = None) -> Awaitable[list[str]]:
        """
        Gets the names of all the IceGrid registries currently registered.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[list[str]]
            The registry names.
        """
        return Admin._op_getAllRegistryNames.invokeAsync(self, ((), context))

    def shutdown(self, context: dict[str, str] | None = None) -> None:
        """
        Shuts down the IceGrid registry.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        """
        return Admin._op_shutdown.invoke(self, ((), context))

    def shutdownAsync(self, context: dict[str, str] | None = None) -> Awaitable[None]:
        """
        Shuts down the IceGrid registry.
        
        Parameters
        ----------
        context : dict[str, str]
            The request context for the invocation.
        
        Returns
        -------
        Awaitable[None]
            An awaitable that is completed when the invocation completes.
        """
        return Admin._op_shutdown.invokeAsync(self, ((), context))

    @staticmethod
    def checkedCast(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> AdminPrx | None:
        return checkedCast(AdminPrx, proxy, facet, context)

    @staticmethod
    def checkedCastAsync(
        proxy: ObjectPrx | None,
        facet: str | None = None,
        context: dict[str, str] | None = None
    ) -> Awaitable[AdminPrx | None ]:
        return checkedCastAsync(AdminPrx, proxy, facet, context)

    @overload
    @staticmethod
    def uncheckedCast(proxy: ObjectPrx, facet: str | None = None) -> AdminPrx:
        ...

    @overload
    @staticmethod
    def uncheckedCast(proxy: None, facet: str | None = None) -> None:
        ...

    @staticmethod
    def uncheckedCast(proxy: ObjectPrx | None, facet: str | None = None) -> AdminPrx | None:
        return uncheckedCast(AdminPrx, proxy, facet)

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::Admin"

IcePy.defineProxy("::IceGrid::Admin", AdminPrx)

class Admin(Object, ABC):
    """
    Provides administrative access to an IceGrid deployment.
    
    Notes
    -----
        The Slice compiler generated this skeleton class from Slice interface ``::IceGrid::Admin``.
    """

    _ice_ids: Sequence[str] = ("::Ice::Object", "::IceGrid::Admin", )
    _op_addApplication: IcePy.Operation
    _op_syncApplication: IcePy.Operation
    _op_updateApplication: IcePy.Operation
    _op_syncApplicationWithoutRestart: IcePy.Operation
    _op_updateApplicationWithoutRestart: IcePy.Operation
    _op_removeApplication: IcePy.Operation
    _op_instantiateServer: IcePy.Operation
    _op_getApplicationInfo: IcePy.Operation
    _op_getDefaultApplicationDescriptor: IcePy.Operation
    _op_getAllApplicationNames: IcePy.Operation
    _op_getServerInfo: IcePy.Operation
    _op_getServerState: IcePy.Operation
    _op_getServerPid: IcePy.Operation
    _op_getServerAdminCategory: IcePy.Operation
    _op_getServerAdmin: IcePy.Operation
    _op_enableServer: IcePy.Operation
    _op_isServerEnabled: IcePy.Operation
    _op_startServer: IcePy.Operation
    _op_stopServer: IcePy.Operation
    _op_sendSignal: IcePy.Operation
    _op_getAllServerIds: IcePy.Operation
    _op_getAdapterInfo: IcePy.Operation
    _op_removeAdapter: IcePy.Operation
    _op_getAllAdapterIds: IcePy.Operation
    _op_addObject: IcePy.Operation
    _op_updateObject: IcePy.Operation
    _op_addObjectWithType: IcePy.Operation
    _op_removeObject: IcePy.Operation
    _op_getObjectInfo: IcePy.Operation
    _op_getObjectInfosByType: IcePy.Operation
    _op_getAllObjectInfos: IcePy.Operation
    _op_pingNode: IcePy.Operation
    _op_getNodeLoad: IcePy.Operation
    _op_getNodeInfo: IcePy.Operation
    _op_getNodeAdmin: IcePy.Operation
    _op_getNodeProcessorSocketCount: IcePy.Operation
    _op_shutdownNode: IcePy.Operation
    _op_getNodeHostname: IcePy.Operation
    _op_getAllNodeNames: IcePy.Operation
    _op_pingRegistry: IcePy.Operation
    _op_getRegistryInfo: IcePy.Operation
    _op_getRegistryAdmin: IcePy.Operation
    _op_shutdownRegistry: IcePy.Operation
    _op_getAllRegistryNames: IcePy.Operation
    _op_shutdown: IcePy.Operation

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::Admin"

    @abstractmethod
    def addApplication(self, descriptor: ApplicationDescriptor, current: Current) -> None | Awaitable[None]:
        """
        Adds an application to IceGrid.
        
        Parameters
        ----------
        descriptor : ApplicationDescriptor
            The application descriptor.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        AccessDeniedException
            Thrown when the session doesn't hold the exclusive lock or when another
            session is holding the lock.
        DeploymentException
            Thrown when the application deployment failed.
        """
        pass

    @abstractmethod
    def syncApplication(self, descriptor: ApplicationDescriptor, current: Current) -> None | Awaitable[None]:
        """
        Synchronizes a deployed application. This operation replaces the current descriptor with a new descriptor.
        
        Parameters
        ----------
        descriptor : ApplicationDescriptor
            The new application descriptor.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        AccessDeniedException
            Thrown when the session doesn't hold the exclusive lock or when another
            session is holding the lock.
        ApplicationNotExistException
            Thrown when the application doesn't exist.
        DeploymentException
            Thrown when the application deployment failed.
        """
        pass

    @abstractmethod
    def updateApplication(self, descriptor: ApplicationUpdateDescriptor, current: Current) -> None | Awaitable[None]:
        """
        Updates a deployed application.
        
        Parameters
        ----------
        descriptor : ApplicationUpdateDescriptor
            The update descriptor.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        AccessDeniedException
            Thrown when the session doesn't hold the exclusive lock or when another
            session is holding the lock.
        ApplicationNotExistException
            Thrown when the application doesn't exist.
        DeploymentException
            Thrown when the application deployment failed.
        """
        pass

    @abstractmethod
    def syncApplicationWithoutRestart(self, descriptor: ApplicationDescriptor, current: Current) -> None | Awaitable[None]:
        """
        Synchronizes a deployed application. This operation replaces the current descriptor with a new descriptor
        only if no server restarts are necessary for the update of the application. If some servers need to be
        restarted, the synchronization is rejected with a DeploymentException.
        
        Parameters
        ----------
        descriptor : ApplicationDescriptor
            The application descriptor.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        AccessDeniedException
            Thrown when the session doesn't hold the exclusive lock or when another
            session is holding the lock.
        ApplicationNotExistException
            Thrown when the application doesn't exist.
        DeploymentException
            Thrown when the application deployment failed.
        """
        pass

    @abstractmethod
    def updateApplicationWithoutRestart(self, descriptor: ApplicationUpdateDescriptor, current: Current) -> None | Awaitable[None]:
        """
        Updates a deployed application. This operation succeeds only when no server restarts are necessary for the
        update of the application. If some servers need to be restarted, the synchronization is rejected with a
        DeploymentException.
        
        Parameters
        ----------
        descriptor : ApplicationUpdateDescriptor
            The update descriptor.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        AccessDeniedException
            Thrown when the session doesn't hold the exclusive lock or when another
            session is holding the lock.
        ApplicationNotExistException
            Thrown when the application doesn't exist.
        DeploymentException
            Thrown when the application deployment failed.
        """
        pass

    @abstractmethod
    def removeApplication(self, name: str, current: Current) -> None | Awaitable[None]:
        """
        Removes an application from IceGrid.
        
        Parameters
        ----------
        name : str
            The application name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        AccessDeniedException
            Thrown when the session doesn't hold the exclusive lock or when another
            session is holding the lock.
        ApplicationNotExistException
            Thrown when the application doesn't exist.
        DeploymentException
            Thrown when the application deployment failed.
        """
        pass

    @abstractmethod
    def instantiateServer(self, application: str, node: str, desc: ServerInstanceDescriptor, current: Current) -> None | Awaitable[None]:
        """
        Instantiates a server template.
        
        Parameters
        ----------
        application : str
            The application name.
        node : str
            The name of the node where the server will be deployed.
        desc : ServerInstanceDescriptor
            The descriptor of the server instance to deploy.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        AccessDeniedException
            Thrown when the session doesn't hold the exclusive lock or when another
            session is holding the lock.
        ApplicationNotExistException
            Thrown when the application doesn't exist.
        DeploymentException
            Thrown when the application deployment failed.
        """
        pass

    @abstractmethod
    def getApplicationInfo(self, name: str, current: Current) -> ApplicationInfo | Awaitable[ApplicationInfo]:
        """
        Gets an application descriptor.
        
        Parameters
        ----------
        name : str
            The application name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ApplicationInfo | Awaitable[ApplicationInfo]
            The application descriptor.
        
        Raises
        ------
        ApplicationNotExistException
            Thrown when the application doesn't exist.
        """
        pass

    @abstractmethod
    def getDefaultApplicationDescriptor(self, current: Current) -> ApplicationDescriptor | Awaitable[ApplicationDescriptor]:
        """
        Gets the default application descriptor.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ApplicationDescriptor | Awaitable[ApplicationDescriptor]
            The default application descriptor.
        
        Raises
        ------
        DeploymentException
            Thrown when the default application descriptor is invalid or unreachable.
        """
        pass

    @abstractmethod
    def getAllApplicationNames(self, current: Current) -> Sequence[str] | Awaitable[Sequence[str]]:
        """
        Gets all the IceGrid applications currently registered.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        Sequence[str] | Awaitable[Sequence[str]]
            The application names.
        """
        pass

    @abstractmethod
    def getServerInfo(self, id: str, current: Current) -> ServerInfo | Awaitable[ServerInfo]:
        """
        Gets information about a server.
        
        Parameters
        ----------
        id : str
            The server ID.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ServerInfo | Awaitable[ServerInfo]
            The server information.
        
        Raises
        ------
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        pass

    @abstractmethod
    def getServerState(self, id: str, current: Current) -> ServerState | Awaitable[ServerState]:
        """
        Gets the state of a server.
        
        Parameters
        ----------
        id : str
            The server ID.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ServerState | Awaitable[ServerState]
            The server state.
        
        Raises
        ------
        DeploymentException
            Thrown when the deployment of the server failed.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        pass

    @abstractmethod
    def getServerPid(self, id: str, current: Current) -> int | Awaitable[int]:
        """
        Gets the system process ID of a server. The process ID is operating system dependent.
        
        Parameters
        ----------
        id : str
            The server ID.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        int | Awaitable[int]
            The process ID.
        
        Raises
        ------
        DeploymentException
            Thrown when the deployment of the server failed.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        pass

    @abstractmethod
    def getServerAdminCategory(self, current: Current) -> str | Awaitable[str]:
        """
        Gets the category for server admin objects. You can manufacture a server admin proxy from the admin proxy by
        changing its identity: use the server ID as name and the returned category as category.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        str | Awaitable[str]
            The category for server admin objects.
        """
        pass

    @abstractmethod
    def getServerAdmin(self, id: str, current: Current) -> ObjectPrx | None | Awaitable[ObjectPrx | None]:
        """
        Gets a proxy to the admin object of a server.
        
        Parameters
        ----------
        id : str
            The server ID.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ObjectPrx | None | Awaitable[ObjectPrx | None]
            A proxy to the admin object of the server. This proxy is never null.
        
        Raises
        ------
        DeploymentException
            Thrown when the deployment of the server failed.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        pass

    @abstractmethod
    def enableServer(self, id: str, enabled: bool, current: Current) -> None | Awaitable[None]:
        """
        Enables or disables a server. A disabled server can't be started on demand or administratively. The enable
        state of the server is not persistent: if the node is shut down and restarted, the server will be enabled by
        default.
        
        Parameters
        ----------
        id : str
            The server ID.
        enabled : bool
            ``true`` to enable the server, ``false`` to disable it.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        DeploymentException
            Thrown when the deployment of the server failed.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        pass

    @abstractmethod
    def isServerEnabled(self, id: str, current: Current) -> bool | Awaitable[bool]:
        """
        Checks if the server is enabled or disabled.
        
        Parameters
        ----------
        id : str
            The server ID.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        bool | Awaitable[bool]
            ``true`` if the server is enabled, ``false`` otherwise.
        
        Raises
        ------
        DeploymentException
            Thrown when the deployment of the server failed.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        pass

    @abstractmethod
    def startServer(self, id: str, current: Current) -> None | Awaitable[None]:
        """
        Starts a server and waits for its activation.
        
        Parameters
        ----------
        id : str
            The server id.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        DeploymentException
            Thrown when the deployment of the server failed.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        ServerStartException
            Thrown when the server startup failed.
        """
        pass

    @abstractmethod
    def stopServer(self, id: str, current: Current) -> None | Awaitable[None]:
        """
        Stops a server.
        
        Parameters
        ----------
        id : str
            The server ID.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        DeploymentException
            Thrown when the deployment of the server failed.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        ServerStopException
            Thrown when the server stop failed.
        """
        pass

    @abstractmethod
    def sendSignal(self, id: str, signal: str, current: Current) -> None | Awaitable[None]:
        """
        Sends a signal to a server.
        
        Parameters
        ----------
        id : str
            The server ID.
        signal : str
            The signal, for example SIGTERM or 15.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        BadSignalException
            Thrown when the signal is not recognized by the target server.
        DeploymentException
            Thrown when the deployment of the server failed.
        NodeUnreachableException
            Thrown when the node is unreachable.
        ServerNotExistException
            Thrown when the server doesn't exist.
        """
        pass

    @abstractmethod
    def getAllServerIds(self, current: Current) -> Sequence[str] | Awaitable[Sequence[str]]:
        """
        Gets the IDs of all the servers registered with IceGrid.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        Sequence[str] | Awaitable[Sequence[str]]
            The server IDs.
        """
        pass

    @abstractmethod
    def getAdapterInfo(self, id: str, current: Current) -> Sequence[AdapterInfo] | Awaitable[Sequence[AdapterInfo]]:
        """
        Gets adapter information for the replica group or adapter with the given ID.
        
        Parameters
        ----------
        id : str
            The adapter or replica group ID.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        Sequence[AdapterInfo] | Awaitable[Sequence[AdapterInfo]]
            A sequence of AdapterInfo. If ``id`` refers to an adapter, this sequence contains a single element.
            If ``id`` refers to a replica group, this sequence contains adapter information for each member of the
            replica group.
        
        Raises
        ------
        AdapterNotExistException
            Thrown when the adapter or replica group doesn't exist.
        """
        pass

    @abstractmethod
    def removeAdapter(self, id: str, current: Current) -> None | Awaitable[None]:
        """
        Removes the adapter with the given ID.
        
        Parameters
        ----------
        id : str
            The adapter ID.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        AdapterNotExistException
            Thrown when the adapter doesn't exist.
        DeploymentException
            Thrown when the application deployment failed.
        """
        pass

    @abstractmethod
    def getAllAdapterIds(self, current: Current) -> Sequence[str] | Awaitable[Sequence[str]]:
        """
        Gets the IDs of all adapters registered with IceGrid.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        Sequence[str] | Awaitable[Sequence[str]]
            The adapter IDs.
        """
        pass

    @abstractmethod
    def addObject(self, obj: ObjectPrx | None, current: Current) -> None | Awaitable[None]:
        """
        Adds an object to the object registry. IceGrid gets the object type by calling ``ice_id`` on ``obj``. The
        object must be reachable.
        
        Parameters
        ----------
        obj : ObjectPrx | None
            A proxy to the object. This proxy is never null.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        DeploymentException
            Thrown when the object can't be added.
        ObjectExistsException
            Thrown when the object is already registered.
        """
        pass

    @abstractmethod
    def updateObject(self, obj: ObjectPrx | None, current: Current) -> None | Awaitable[None]:
        """
        Updates an object in the object registry. Only objects added with this interface can be updated with this
        operation. Objects added with deployment descriptors should be updated with the deployment mechanism.
        
        Parameters
        ----------
        obj : ObjectPrx | None
            A proxy to the object. This proxy is never null.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        DeploymentException
            Thrown when the object can't be updated.
        ObjectNotRegisteredException
            Thrown when the object isn't registered with the registry.
        """
        pass

    @abstractmethod
    def addObjectWithType(self, obj: ObjectPrx | None, type: str, current: Current) -> None | Awaitable[None]:
        """
        Adds an object to the object registry and explicitly specifies its type.
        
        Parameters
        ----------
        obj : ObjectPrx | None
            The object to be added to the registry. The proxy is never null.
        type : str
            The type name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        DeploymentException
            Thrown when the application deployment failed.
        ObjectExistsException
            Thrown when the object is already registered.
        """
        pass

    @abstractmethod
    def removeObject(self, id: Identity, current: Current) -> None | Awaitable[None]:
        """
        Removes an object from the object registry. Only objects added with this interface can be removed with this
        operation. Objects added with deployment descriptors should be removed with the deployment mechanism.
        
        Parameters
        ----------
        id : Identity
            The identity of the object to remove.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        DeploymentException
            Thrown when the object can't be removed.
        ObjectNotRegisteredException
            Thrown when the object isn't registered with the registry.
        """
        pass

    @abstractmethod
    def getObjectInfo(self, id: Identity, current: Current) -> ObjectInfo | Awaitable[ObjectInfo]:
        """
        Gets the object info for the object.
        
        Parameters
        ----------
        id : Identity
            The identity of the object.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ObjectInfo | Awaitable[ObjectInfo]
            The object info.
        
        Raises
        ------
        ObjectNotRegisteredException
            Thrown when the object isn't registered with the registry.
        """
        pass

    @abstractmethod
    def getObjectInfosByType(self, type: str, current: Current) -> Sequence[ObjectInfo] | Awaitable[Sequence[ObjectInfo]]:
        """
        Gets the object info of all the registered objects with a given type.
        
        Parameters
        ----------
        type : str
            The type name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        Sequence[ObjectInfo] | Awaitable[Sequence[ObjectInfo]]
            The object infos.
        """
        pass

    @abstractmethod
    def getAllObjectInfos(self, expr: str, current: Current) -> Sequence[ObjectInfo] | Awaitable[Sequence[ObjectInfo]]:
        """
        Gets the object info of all the registered objects whose stringified identities match the given expression.
        
        Parameters
        ----------
        expr : str
            The expression to match against the stringified identities of registered objects. The expression
            may contain a trailing wildcard (``*``) character.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        Sequence[ObjectInfo] | Awaitable[Sequence[ObjectInfo]]
            All the object infos with a stringified identity matching the given expression.
        """
        pass

    @abstractmethod
    def pingNode(self, name: str, current: Current) -> bool | Awaitable[bool]:
        """
        Pings an IceGrid node to see if it is active.
        
        Parameters
        ----------
        name : str
            The node name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        bool | Awaitable[bool]
            ``true`` if the node ping succeeded, ``false`` otherwise.
        
        Raises
        ------
        NodeNotExistException
            Thrown when the node doesn't exist.
        """
        pass

    @abstractmethod
    def getNodeLoad(self, name: str, current: Current) -> LoadInfo | Awaitable[LoadInfo]:
        """
        Gets the load averages of a node.
        
        Parameters
        ----------
        name : str
            The node name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        LoadInfo | Awaitable[LoadInfo]
            The node load information.
        
        Raises
        ------
        NodeNotExistException
            Thrown when the node doesn't exist.
        NodeUnreachableException
            Thrown when the node is unreachable.
        """
        pass

    @abstractmethod
    def getNodeInfo(self, name: str, current: Current) -> NodeInfo | Awaitable[NodeInfo]:
        """
        Gets the node information of a node.
        
        Parameters
        ----------
        name : str
            The node name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        NodeInfo | Awaitable[NodeInfo]
            The node information.
        
        Raises
        ------
        NodeNotExistException
            Thrown when the node doesn't exist.
        NodeUnreachableException
            Thrown when the node is unreachable.
        """
        pass

    @abstractmethod
    def getNodeAdmin(self, name: str, current: Current) -> ObjectPrx | None | Awaitable[ObjectPrx | None]:
        """
        Gets a proxy to the admin object of an IceGrid node.
        
        Parameters
        ----------
        name : str
            The IceGrid node name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ObjectPrx | None | Awaitable[ObjectPrx | None]
            A proxy to the IceGrid node's admin object. This proxy is never null.
        
        Raises
        ------
        NodeNotExistException
            Thrown when the node doesn't exist.
        NodeUnreachableException
            Thrown when the node is unreachable.
        """
        pass

    @abstractmethod
    def getNodeProcessorSocketCount(self, name: str, current: Current) -> int | Awaitable[int]:
        """
        Gets the number of physical processor sockets in the computer where an IceGrid node is deployed.
        Note that this operation returns 1 on operating systems where this can't be automatically determined and
        where the ``IceGrid.Node.ProcessorSocketCount`` property for the node is not set.
        
        Parameters
        ----------
        name : str
            The node name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        int | Awaitable[int]
            The number of processor sockets or 1 if the number of sockets can't be determined.
        
        Raises
        ------
        NodeNotExistException
            Thrown when the node doesn't exist.
        NodeUnreachableException
            Thrown when the node is unreachable.
        """
        pass

    @abstractmethod
    def shutdownNode(self, name: str, current: Current) -> None | Awaitable[None]:
        """
        Shuts down an IceGrid node.
        
        Parameters
        ----------
        name : str
            The node name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        NodeNotExistException
            Thrown when the node doesn't exist.
        NodeUnreachableException
            Thrown when the node is unreachable.
        """
        pass

    @abstractmethod
    def getNodeHostname(self, name: str, current: Current) -> str | Awaitable[str]:
        """
        Get the hostname of a node.
        
        Parameters
        ----------
        name : str
            The node name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        str | Awaitable[str]
            The node hostname.
        
        Raises
        ------
        NodeNotExistException
            Thrown when the node doesn't exist.
        NodeUnreachableException
            Thrown when the node is unreachable.
        """
        pass

    @abstractmethod
    def getAllNodeNames(self, current: Current) -> Sequence[str] | Awaitable[Sequence[str]]:
        """
        Gets the names of all IceGrid nodes currently registered.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        Sequence[str] | Awaitable[Sequence[str]]
            The node names.
        """
        pass

    @abstractmethod
    def pingRegistry(self, name: str, current: Current) -> bool | Awaitable[bool]:
        """
        Pings an IceGrid registry to see if it is active.
        
        Parameters
        ----------
        name : str
            The registry name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        bool | Awaitable[bool]
            ``true`` if the registry ping succeeded, ``false`` otherwise.
        
        Raises
        ------
        RegistryNotExistException
            Thrown when the registry doesn't exist.
        """
        pass

    @abstractmethod
    def getRegistryInfo(self, name: str, current: Current) -> RegistryInfo | Awaitable[RegistryInfo]:
        """
        Gets the registry information of an IceGrid registry.
        
        Parameters
        ----------
        name : str
            The registry name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        RegistryInfo | Awaitable[RegistryInfo]
            The registry information.
        
        Raises
        ------
        RegistryNotExistException
            Thrown when the registry doesn't exist.
        RegistryUnreachableException
            Thrown when the registry is unreachable.
        """
        pass

    @abstractmethod
    def getRegistryAdmin(self, name: str, current: Current) -> ObjectPrx | None | Awaitable[ObjectPrx | None]:
        """
        Gets a proxy to the admin object of an IceGrid registry.
        
        Parameters
        ----------
        name : str
            The registry name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        ObjectPrx | None | Awaitable[ObjectPrx | None]
            A proxy to the admin object of an IceGrid registry. This proxy is never null.
        
        Raises
        ------
        RegistryNotExistException
            Thrown when the registry doesn't exist.
        """
        pass

    @abstractmethod
    def shutdownRegistry(self, name: str, current: Current) -> None | Awaitable[None]:
        """
        Shuts down an IceGrid registry.
        
        Parameters
        ----------
        name : str
            The registry name.
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        None | Awaitable[None]
            None or an awaitable that completes when the dispatch completes.
        
        Raises
        ------
        RegistryNotExistException
            Thrown when the registry doesn't exist.
        RegistryUnreachableException
            Thrown when the registry is unreachable.
        """
        pass

    @abstractmethod
    def getAllRegistryNames(self, current: Current) -> Sequence[str] | Awaitable[Sequence[str]]:
        """
        Gets the names of all the IceGrid registries currently registered.
        
        Parameters
        ----------
        current : Ice.Current
            The Current object for the dispatch.
        
        Returns
        -------
        Sequence[str] | Awaitable[Sequence[str]]
            The registry names.
        """
        pass

    @abstractmethod
    def shutdown(self, current: Current) -> None | Awaitable[None]:
        """
        Shuts down the IceGrid registry.
        
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

Admin._op_addApplication = IcePy.Operation(
    "addApplication",
    "addApplication",
    OperationMode.Normal,
    None,
    (),
    (((), _IceGrid_ApplicationDescriptor_t, False, 0),),
    (),
    None,
    (_IceGrid_AccessDeniedException_t, _IceGrid_DeploymentException_t))

Admin._op_syncApplication = IcePy.Operation(
    "syncApplication",
    "syncApplication",
    OperationMode.Normal,
    None,
    (),
    (((), _IceGrid_ApplicationDescriptor_t, False, 0),),
    (),
    None,
    (_IceGrid_AccessDeniedException_t, _IceGrid_DeploymentException_t, _IceGrid_ApplicationNotExistException_t))

Admin._op_updateApplication = IcePy.Operation(
    "updateApplication",
    "updateApplication",
    OperationMode.Normal,
    None,
    (),
    (((), _IceGrid_ApplicationUpdateDescriptor_t, False, 0),),
    (),
    None,
    (_IceGrid_AccessDeniedException_t, _IceGrid_DeploymentException_t, _IceGrid_ApplicationNotExistException_t))

Admin._op_syncApplicationWithoutRestart = IcePy.Operation(
    "syncApplicationWithoutRestart",
    "syncApplicationWithoutRestart",
    OperationMode.Normal,
    None,
    (),
    (((), _IceGrid_ApplicationDescriptor_t, False, 0),),
    (),
    None,
    (_IceGrid_AccessDeniedException_t, _IceGrid_DeploymentException_t, _IceGrid_ApplicationNotExistException_t))

Admin._op_updateApplicationWithoutRestart = IcePy.Operation(
    "updateApplicationWithoutRestart",
    "updateApplicationWithoutRestart",
    OperationMode.Normal,
    None,
    (),
    (((), _IceGrid_ApplicationUpdateDescriptor_t, False, 0),),
    (),
    None,
    (_IceGrid_AccessDeniedException_t, _IceGrid_DeploymentException_t, _IceGrid_ApplicationNotExistException_t))

Admin._op_removeApplication = IcePy.Operation(
    "removeApplication",
    "removeApplication",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    None,
    (_IceGrid_AccessDeniedException_t, _IceGrid_DeploymentException_t, _IceGrid_ApplicationNotExistException_t))

Admin._op_instantiateServer = IcePy.Operation(
    "instantiateServer",
    "instantiateServer",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0), ((), _IceGrid_ServerInstanceDescriptor_t, False, 0)),
    (),
    None,
    (_IceGrid_AccessDeniedException_t, _IceGrid_ApplicationNotExistException_t, _IceGrid_DeploymentException_t))

Admin._op_getApplicationInfo = IcePy.Operation(
    "getApplicationInfo",
    "getApplicationInfo",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _IceGrid_ApplicationInfo_t, False, 0),
    (_IceGrid_ApplicationNotExistException_t,))

Admin._op_getDefaultApplicationDescriptor = IcePy.Operation(
    "getDefaultApplicationDescriptor",
    "getDefaultApplicationDescriptor",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), _IceGrid_ApplicationDescriptor_t, False, 0),
    (_IceGrid_DeploymentException_t,))

Admin._op_getAllApplicationNames = IcePy.Operation(
    "getAllApplicationNames",
    "getAllApplicationNames",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), _Ice_StringSeq_t, False, 0),
    ())

Admin._op_getServerInfo = IcePy.Operation(
    "getServerInfo",
    "getServerInfo",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _IceGrid_ServerInfo_t, False, 0),
    (_IceGrid_ServerNotExistException_t,))

Admin._op_getServerState = IcePy.Operation(
    "getServerState",
    "getServerState",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _IceGrid_ServerState_t, False, 0),
    (_IceGrid_ServerNotExistException_t, _IceGrid_NodeUnreachableException_t, _IceGrid_DeploymentException_t))

Admin._op_getServerPid = IcePy.Operation(
    "getServerPid",
    "getServerPid",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), IcePy._t_int, False, 0),
    (_IceGrid_ServerNotExistException_t, _IceGrid_NodeUnreachableException_t, _IceGrid_DeploymentException_t))

Admin._op_getServerAdminCategory = IcePy.Operation(
    "getServerAdminCategory",
    "getServerAdminCategory",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), IcePy._t_string, False, 0),
    ())

Admin._op_getServerAdmin = IcePy.Operation(
    "getServerAdmin",
    "getServerAdmin",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _Ice_ObjectPrx_t, False, 0),
    (_IceGrid_ServerNotExistException_t, _IceGrid_NodeUnreachableException_t, _IceGrid_DeploymentException_t))

Admin._op_enableServer = IcePy.Operation(
    "enableServer",
    "enableServer",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), IcePy._t_bool, False, 0)),
    (),
    None,
    (_IceGrid_ServerNotExistException_t, _IceGrid_NodeUnreachableException_t, _IceGrid_DeploymentException_t))

Admin._op_isServerEnabled = IcePy.Operation(
    "isServerEnabled",
    "isServerEnabled",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), IcePy._t_bool, False, 0),
    (_IceGrid_ServerNotExistException_t, _IceGrid_NodeUnreachableException_t, _IceGrid_DeploymentException_t))

Admin._op_startServer = IcePy.Operation(
    "startServer",
    "startServer",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    None,
    (_IceGrid_ServerNotExistException_t, _IceGrid_ServerStartException_t, _IceGrid_NodeUnreachableException_t, _IceGrid_DeploymentException_t))

Admin._op_stopServer = IcePy.Operation(
    "stopServer",
    "stopServer",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    None,
    (_IceGrid_ServerNotExistException_t, _IceGrid_ServerStopException_t, _IceGrid_NodeUnreachableException_t, _IceGrid_DeploymentException_t))

Admin._op_sendSignal = IcePy.Operation(
    "sendSignal",
    "sendSignal",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0)),
    (),
    None,
    (_IceGrid_ServerNotExistException_t, _IceGrid_NodeUnreachableException_t, _IceGrid_DeploymentException_t, _IceGrid_BadSignalException_t))

Admin._op_getAllServerIds = IcePy.Operation(
    "getAllServerIds",
    "getAllServerIds",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), _Ice_StringSeq_t, False, 0),
    ())

Admin._op_getAdapterInfo = IcePy.Operation(
    "getAdapterInfo",
    "getAdapterInfo",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _IceGrid_AdapterInfoSeq_t, False, 0),
    (_IceGrid_AdapterNotExistException_t,))

Admin._op_removeAdapter = IcePy.Operation(
    "removeAdapter",
    "removeAdapter",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    None,
    (_IceGrid_AdapterNotExistException_t, _IceGrid_DeploymentException_t))

Admin._op_getAllAdapterIds = IcePy.Operation(
    "getAllAdapterIds",
    "getAllAdapterIds",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), _Ice_StringSeq_t, False, 0),
    ())

Admin._op_addObject = IcePy.Operation(
    "addObject",
    "addObject",
    OperationMode.Normal,
    None,
    (),
    (((), _Ice_ObjectPrx_t, False, 0),),
    (),
    None,
    (_IceGrid_ObjectExistsException_t, _IceGrid_DeploymentException_t))

Admin._op_updateObject = IcePy.Operation(
    "updateObject",
    "updateObject",
    OperationMode.Normal,
    None,
    (),
    (((), _Ice_ObjectPrx_t, False, 0),),
    (),
    None,
    (_IceGrid_ObjectNotRegisteredException_t, _IceGrid_DeploymentException_t))

Admin._op_addObjectWithType = IcePy.Operation(
    "addObjectWithType",
    "addObjectWithType",
    OperationMode.Normal,
    None,
    (),
    (((), _Ice_ObjectPrx_t, False, 0), ((), IcePy._t_string, False, 0)),
    (),
    None,
    (_IceGrid_ObjectExistsException_t, _IceGrid_DeploymentException_t))

Admin._op_removeObject = IcePy.Operation(
    "removeObject",
    "removeObject",
    OperationMode.Normal,
    None,
    (),
    (((), _Ice_Identity_t, False, 0),),
    (),
    None,
    (_IceGrid_ObjectNotRegisteredException_t, _IceGrid_DeploymentException_t))

Admin._op_getObjectInfo = IcePy.Operation(
    "getObjectInfo",
    "getObjectInfo",
    OperationMode.Idempotent,
    None,
    (),
    (((), _Ice_Identity_t, False, 0),),
    (),
    ((), _IceGrid_ObjectInfo_t, False, 0),
    (_IceGrid_ObjectNotRegisteredException_t,))

Admin._op_getObjectInfosByType = IcePy.Operation(
    "getObjectInfosByType",
    "getObjectInfosByType",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _IceGrid_ObjectInfoSeq_t, False, 0),
    ())

Admin._op_getAllObjectInfos = IcePy.Operation(
    "getAllObjectInfos",
    "getAllObjectInfos",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _IceGrid_ObjectInfoSeq_t, False, 0),
    ())

Admin._op_pingNode = IcePy.Operation(
    "pingNode",
    "pingNode",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), IcePy._t_bool, False, 0),
    (_IceGrid_NodeNotExistException_t,))

Admin._op_getNodeLoad = IcePy.Operation(
    "getNodeLoad",
    "getNodeLoad",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _IceGrid_LoadInfo_t, False, 0),
    (_IceGrid_NodeNotExistException_t, _IceGrid_NodeUnreachableException_t))

Admin._op_getNodeInfo = IcePy.Operation(
    "getNodeInfo",
    "getNodeInfo",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _IceGrid_NodeInfo_t, False, 0),
    (_IceGrid_NodeNotExistException_t, _IceGrid_NodeUnreachableException_t))

Admin._op_getNodeAdmin = IcePy.Operation(
    "getNodeAdmin",
    "getNodeAdmin",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _Ice_ObjectPrx_t, False, 0),
    (_IceGrid_NodeNotExistException_t, _IceGrid_NodeUnreachableException_t))

Admin._op_getNodeProcessorSocketCount = IcePy.Operation(
    "getNodeProcessorSocketCount",
    "getNodeProcessorSocketCount",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), IcePy._t_int, False, 0),
    (_IceGrid_NodeNotExistException_t, _IceGrid_NodeUnreachableException_t))

Admin._op_shutdownNode = IcePy.Operation(
    "shutdownNode",
    "shutdownNode",
    OperationMode.Normal,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    None,
    (_IceGrid_NodeNotExistException_t, _IceGrid_NodeUnreachableException_t))

Admin._op_getNodeHostname = IcePy.Operation(
    "getNodeHostname",
    "getNodeHostname",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), IcePy._t_string, False, 0),
    (_IceGrid_NodeNotExistException_t, _IceGrid_NodeUnreachableException_t))

Admin._op_getAllNodeNames = IcePy.Operation(
    "getAllNodeNames",
    "getAllNodeNames",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), _Ice_StringSeq_t, False, 0),
    ())

Admin._op_pingRegistry = IcePy.Operation(
    "pingRegistry",
    "pingRegistry",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), IcePy._t_bool, False, 0),
    (_IceGrid_RegistryNotExistException_t,))

Admin._op_getRegistryInfo = IcePy.Operation(
    "getRegistryInfo",
    "getRegistryInfo",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _IceGrid_RegistryInfo_t, False, 0),
    (_IceGrid_RegistryNotExistException_t, _IceGrid_RegistryUnreachableException_t))

Admin._op_getRegistryAdmin = IcePy.Operation(
    "getRegistryAdmin",
    "getRegistryAdmin",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    ((), _Ice_ObjectPrx_t, False, 0),
    (_IceGrid_RegistryNotExistException_t,))

Admin._op_shutdownRegistry = IcePy.Operation(
    "shutdownRegistry",
    "shutdownRegistry",
    OperationMode.Idempotent,
    None,
    (),
    (((), IcePy._t_string, False, 0),),
    (),
    None,
    (_IceGrid_RegistryNotExistException_t, _IceGrid_RegistryUnreachableException_t))

Admin._op_getAllRegistryNames = IcePy.Operation(
    "getAllRegistryNames",
    "getAllRegistryNames",
    OperationMode.Idempotent,
    None,
    (),
    (),
    (),
    ((), _Ice_StringSeq_t, False, 0),
    ())

Admin._op_shutdown = IcePy.Operation(
    "shutdown",
    "shutdown",
    OperationMode.Normal,
    None,
    (),
    (),
    (),
    None,
    ())

__all__ = ["Admin", "AdminPrx", "_IceGrid_AdminPrx_t"]
