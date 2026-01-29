import typing

from ._auth import Auth
from ._auth import AuthConfig as Config
from ._generated._region import Region
from ._generated._service import Service
from ._generated._service_endpoint_templates import (
    SERVICE_ENDPOINT_TEMPLATES as _SERVICE_ENDPOINT_TEMPLATES,
)
from ._generated._service_specs import SERVICE_SPECS as _SERVICE_SPECS

if typing.TYPE_CHECKING:
    import httpx


def get_auth(config: Config) -> Auth:
    return Auth.create(
        Config(
            retry_start_delay=config.retry_start_delay,
            retry_max_delay=config.retry_max_delay,
            retry_timeout=config.retry_timeout,
            tenant_id=config.tenant_id,
            user_id=config.user_id,
            api_key_fingerprint=config.api_key_fingerprint,
            api_private_key_pem=config.api_private_key_pem,
        )
    )


def get_base_url(service: Service, region: Region) -> str:
    endpoint = _SERVICE_ENDPOINT_TEMPLATES.get(service.value)
    if endpoint is None:
        msg = 'Cannot find endpoint template for service'
        raise KeyError(msg, service)

    return endpoint.format(region=region.value)


def get_openapi_spec_url(service: Service) -> list[str]:
    specs = _SERVICE_SPECS.get(service.value)
    if specs is None:
        msg = 'Cannot find specs for service'
        raise KeyError(msg, service)

    return specs


type Client = httpx.AsyncClient | httpx.Client


def setup_client(client: Client, service: Service, region: Region, config: Config) -> None:
    client.base_url = get_base_url(service, region)
    client.auth = get_auth(config)


__all__ = [
    'Auth',
    'Client',
    'Config',
    'Region',
    'Service',
    'get_auth',
    'get_base_url',
    'get_openapi_spec_url',
    'setup_client',
]
