import contextlib
import dataclasses
import typing

import httpx
import pydantic

from ._util import GenericRetrier, RetryConfig, RetrySleep


class OciError(pydantic.BaseModel, frozen=True):
    code: str
    message: str


# https://docs.oracle.com/en-us/iaas/Content/API/References/apierrors.htm
_RETRIABLE_ERROR_CODES = frozenset(
    [
        'ExternalServerIncorrectState',
        'IncorrectState',
        'TooManyRequests',
        'InternalServerError',
        'ExternalServerUnreachable',
        'ExternalServerTimeout',
        'ExternalServerInvalidResponse',
        'ServiceUnavailable',
    ]
)

# https://docs.oracle.com/en-us/iaas/Content/API/References/apierrors.htm
_RETRIABLE_STATUSES = frozenset([409, 429, 500, 503])


def _get_retriable_error(response: httpx.Response) -> OciError | None:
    if response.status_code not in _RETRIABLE_STATUSES:
        return None

    try:
        error = OciError.model_validate_json(response.content)
    except pydantic.ValidationError:
        return None

    if error.code not in _RETRIABLE_ERROR_CODES:
        return None

    return error


@dataclasses.dataclass(frozen=True, slots=True)
class Retrier:
    _generic: GenericRetrier[httpx.Response, OciError]

    @staticmethod
    @contextlib.contextmanager
    def create(request: httpx.Request, config: RetryConfig) -> 'typing.Iterator[Retrier]':
        with GenericRetrier[httpx.Response, OciError].create(
            action=f'Api call {request.method} {request.url}',
            config=config,
            errorer=_get_retriable_error,
        ) as generic:
            yield Retrier(generic)

    def retry(self, response: httpx.Response) -> httpx.Response | RetrySleep:
        return self._generic.retry(response)

    def should_read_body(self, response: httpx.Response) -> bool:
        return response.status_code in _RETRIABLE_STATUSES
