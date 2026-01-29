import base64
import dataclasses
import email.utils
import typing

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.types import rsa
from cryptography.hazmat.primitives.hashes import SHA256

from ._util import compute_sha256

type _RequiredHeaders = typing.Mapping[str, str]


def _has_body(request: httpx.Request) -> bool:
    return request.method.lower() in ('post', 'put', 'patch')


def _target(request: httpx.Request) -> str:
    target = f'{request.method.lower()} {request.url.path}'
    query = request.url.query.decode()
    if query:
        target += f'?{query}'
    return target


def _required_headers(request: httpx.Request) -> _RequiredHeaders:
    res: _RequiredHeaders = {}

    res['(request-target)'] = _target(request)
    res['date'] = email.utils.formatdate(usegmt=True)
    res['host'] = request.url.netloc.decode()

    if (content_type := request.headers.get('content-type')) is not None:
        res['content-type'] = content_type

    if _has_body(request):
        res['content-length'] = str(len(request.content))
        res['x-content-sha256'] = compute_sha256(request.content)

    return res


@dataclasses.dataclass(frozen=True, slots=True)
class SignerConfig:
    tenant_id: str
    user_id: str
    api_key_fingerprint: str
    api_private_key_pem: str


@dataclasses.dataclass(frozen=True, slots=True)
class Signer:
    _config: SignerConfig
    _api_private_key: rsa.RSAPrivateKey

    @staticmethod
    def create(config: SignerConfig) -> 'Signer':
        private_key = serialization.load_pem_private_key(
            config.api_private_key_pem.encode('ascii'), None
        )
        if not isinstance(private_key, rsa.RSAPrivateKey):
            msg = f'The private key should be an RSA key, but is a {private_key.__class__}'
            raise TypeError(msg)
        return Signer(config, private_key)

    def _get_key_id(self) -> str:
        return f'{self._config.tenant_id}/{self._config.user_id}/{self._config.api_key_fingerprint}'

    def _get_signature_item(self, required_headers: _RequiredHeaders) -> str:
        return base64.b64encode(
            self._api_private_key.sign(
                '\n'.join(f'{k}: {v}' for (k, v) in required_headers.items()).encode('ascii'),
                padding.PKCS1v15(),
                SHA256(),
            )
        ).decode('ascii')

    def _get_signature(self, required_headers: _RequiredHeaders) -> str:
        return 'Signature ' + ','.join(
            f'{k}="{v}"'
            for (k, v) in {
                'algorithm': 'rsa-sha256',
                'version': '1',
                'headers': ' '.join(required_headers),
                'keyId': self._get_key_id(),
                'signature': self._get_signature_item(required_headers),
            }.items()
        )

    def sign(self, request: httpx.Request) -> None:
        required_headers = _required_headers(request)
        request.headers['authorization'] = self._get_signature(required_headers)
        request.headers.update({k: v for k, v in required_headers.items() if not k.startswith('(')})
