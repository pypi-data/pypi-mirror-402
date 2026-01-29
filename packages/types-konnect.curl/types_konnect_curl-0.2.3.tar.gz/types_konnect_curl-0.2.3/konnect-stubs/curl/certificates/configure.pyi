from ..abc import ConfigHandle
from .encodings import AsciiArmored, Certificate, Encoding, Pkcs12, PrivateKey
from .files import EncodedFile
from pathlib import Path
from typing import TypeAlias, TypeVar, overload

__all__ = ['CertificateSource', 'PrivateKeySource', 'add_ca_certificate', 'add_client_certificate']

ContainerT = TypeVar('ContainerT', AsciiArmored, Pkcs12)
EncodedT = TypeVar('EncodedT', bound=Encoding)
RawT = TypeVar('RawT', Certificate, PrivateKey)
CommonEncodedSource: TypeAlias = AsciiArmored | Pkcs12 | EncodedFile[AsciiArmored] | EncodedFile[Pkcs12]
EncodedSource: TypeAlias = CommonEncodedSource | RawT | EncodedFile[RawT]
CertificateSource: TypeAlias = EncodedSource[Certificate]
PrivateKeySource: TypeAlias = EncodedSource[PrivateKey]

def add_ca_certificate(handle: ConfigHandle, cert_source: CertificateSource | Path) -> None: ...
@overload
def add_client_certificate(handle: ConfigHandle, cert: CertificateSource, key: PrivateKeySource) -> None: ...
@overload
def add_client_certificate(handle: ConfigHandle, cert: CommonEncodedSource, key: None = None) -> None: ...
