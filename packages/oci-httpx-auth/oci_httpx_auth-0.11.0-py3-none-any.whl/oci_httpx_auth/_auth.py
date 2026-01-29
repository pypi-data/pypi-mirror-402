import dataclasses
import datetime
import typing

import httpx
import pydantic

from ._retrier import Retrier, RetryConfig, RetrySleep
from ._signer import Signer, SignerConfig


class AuthConfig(pydantic.BaseModel):
    tenant_id: str
    user_id: str
    api_key_fingerprint: str
    api_private_key_pem: str
    retry_start_delay: datetime.timedelta = datetime.timedelta(seconds=1)
    retry_max_delay: datetime.timedelta = datetime.timedelta(minutes=1)
    retry_timeout: datetime.timedelta = datetime.timedelta(minutes=10)


@dataclasses.dataclass(frozen=True, slots=True)
class Auth(httpx.Auth):
    signer: Signer
    retry_config: RetryConfig

    @staticmethod
    def create(config: AuthConfig) -> 'Auth':
        signer_config = SignerConfig(
            tenant_id=config.tenant_id,
            user_id=config.user_id,
            api_key_fingerprint=config.api_key_fingerprint,
            api_private_key_pem=config.api_private_key_pem,
        )
        retry_config = RetryConfig(
            start_delay=config.retry_start_delay,
            max_delay=config.retry_max_delay,
            timeout=config.retry_timeout,
        )
        return Auth(Signer.create(signer_config), retry_config)

    def sync_auth_flow(
        self, request: httpx.Request
    ) -> typing.Generator[httpx.Request, httpx.Response, None]:
        request.read()
        self.signer.sign(request)
        with Retrier.create(request, self.retry_config) as retrier:
            while True:
                response = yield request
                if retrier.should_read_body(response):
                    response.read()
                match retrier.retry(response):
                    case RetrySleep() as sleep:
                        sleep.sync()
                    case _:
                        return

    async def async_auth_flow(
        self, request: httpx.Request
    ) -> typing.AsyncGenerator[httpx.Request, httpx.Response]:
        await request.aread()
        self.signer.sign(request)
        with Retrier.create(request, self.retry_config) as retrier:
            while True:
                response = yield request
                if retrier.should_read_body(response):
                    await response.aread()
                match retrier.retry(response):
                    case RetrySleep() as sleep:
                        await sleep.asyncio()
                    case _:
                        return
