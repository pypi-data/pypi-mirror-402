# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.StringSeq import _Ice_StringSeq_t

from IceGrid.CommunicatorDescriptor import CommunicatorDescriptor

from IceGrid.CommunicatorDescriptor_forward import _IceGrid_CommunicatorDescriptor_t

from IceGrid.DistributionDescriptor import DistributionDescriptor
from IceGrid.DistributionDescriptor import _IceGrid_DistributionDescriptor_t

from IceGrid.ServerDescriptor_forward import _IceGrid_ServerDescriptor_t

from dataclasses import dataclass
from dataclasses import field

@dataclass(eq=False)
class ServerDescriptor(CommunicatorDescriptor):
    """
    Describes an Ice server.
    
    Attributes
    ----------
    id : str
        The server ID.
    exe : str
        The path of the server executable.
    iceVersion : str
        The Ice version used by this server. This is only required if backward compatibility with servers using old
        Ice versions is needed (otherwise the registry assumes the server is using the same Ice version as the
        registry itself). For example ``"3.7.5"``.
    pwd : str
        The path to the server working directory.
    options : list[str]
        The command line options to pass to the server executable.
    envs : list[str]
        The server environment variables.
    activation : str
        The server activation mode. Possible values are ``"on-demand"`` and ``"manual"``.
    activationTimeout : str
        The activation timeout. It's an integer (in string format) that represents the number of seconds to wait for
        activation.
    deactivationTimeout : str
        The deactivation timeout. It's an integer (in string format) that represents the number of seconds to wait
        for deactivation.
    applicationDistrib : bool
        Specifies if the server depends on the application distribution.
    distrib : DistributionDescriptor
        The distribution descriptor.
    allocatable : bool
        Specifies if the server is allocatable.
    user : str
        The user account used to run the server.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice class ``::IceGrid::ServerDescriptor``.
    """
    id: str = ""
    exe: str = ""
    iceVersion: str = ""
    pwd: str = ""
    options: list[str] = field(default_factory=list)
    envs: list[str] = field(default_factory=list)
    activation: str = ""
    activationTimeout: str = ""
    deactivationTimeout: str = ""
    applicationDistrib: bool = False
    distrib: DistributionDescriptor = field(default_factory=DistributionDescriptor)
    allocatable: bool = False
    user: str = ""

    @staticmethod
    def ice_staticId() -> str:
        return "::IceGrid::ServerDescriptor"

_IceGrid_ServerDescriptor_t = IcePy.defineValue(
    "::IceGrid::ServerDescriptor",
    ServerDescriptor,
    -1,
    (),
    False,
    _IceGrid_CommunicatorDescriptor_t,
    (
        ("id", (), IcePy._t_string, False, 0),
        ("exe", (), IcePy._t_string, False, 0),
        ("iceVersion", (), IcePy._t_string, False, 0),
        ("pwd", (), IcePy._t_string, False, 0),
        ("options", (), _Ice_StringSeq_t, False, 0),
        ("envs", (), _Ice_StringSeq_t, False, 0),
        ("activation", (), IcePy._t_string, False, 0),
        ("activationTimeout", (), IcePy._t_string, False, 0),
        ("deactivationTimeout", (), IcePy._t_string, False, 0),
        ("applicationDistrib", (), IcePy._t_bool, False, 0),
        ("distrib", (), _IceGrid_DistributionDescriptor_t, False, 0),
        ("allocatable", (), IcePy._t_bool, False, 0),
        ("user", (), IcePy._t_string, False, 0)
    ))

setattr(ServerDescriptor, '_ice_type', _IceGrid_ServerDescriptor_t)

__all__ = ["ServerDescriptor", "_IceGrid_ServerDescriptor_t"]
