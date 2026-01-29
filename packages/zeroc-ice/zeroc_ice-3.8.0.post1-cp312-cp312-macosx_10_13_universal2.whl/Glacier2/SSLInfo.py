# Copyright (c) ZeroC, Inc.

# slice2py version 3.8.0

from __future__ import annotations
import IcePy

from Ice.StringSeq import _Ice_StringSeq_t

from dataclasses import dataclass
from dataclasses import field


@dataclass
class SSLInfo:
    """
    Represents information gathered from an incoming SSL connection and used for authentication and authorization.
    
    Attributes
    ----------
    remoteHost : str
        The remote host.
    remotePort : int
        The remote port.
    localHost : str
        The router's host.
    localPort : int
        The router's port.
    cipher : str
        The negotiated cipher suite.
    certs : list[str]
        The certificate chain.
    
    Notes
    -----
        The Slice compiler generated this dataclass from Slice struct ``::Glacier2::SSLInfo``.
    
    See Also
    --------
        :class:`Glacier2.SSLPermissionsVerifierPrx`
    """
    remoteHost: str = ""
    remotePort: int = 0
    localHost: str = ""
    localPort: int = 0
    cipher: str = ""
    certs: list[str] = field(default_factory=list)

_Glacier2_SSLInfo_t = IcePy.defineStruct(
    "::Glacier2::SSLInfo",
    SSLInfo,
    (),
    (
        ("remoteHost", (), IcePy._t_string),
        ("remotePort", (), IcePy._t_int),
        ("localHost", (), IcePy._t_string),
        ("localPort", (), IcePy._t_int),
        ("cipher", (), IcePy._t_string),
        ("certs", (), _Ice_StringSeq_t)
    ))

__all__ = ["SSLInfo", "_Glacier2_SSLInfo_t"]
