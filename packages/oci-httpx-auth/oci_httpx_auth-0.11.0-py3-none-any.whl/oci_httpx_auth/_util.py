import asyncio
import base64
import collections
import contextlib
import dataclasses
import datetime
import hashlib
import time
import typing

# DATETIMES


def format_timdelta(td: datetime.timedelta) -> str:
    return format_timdelta_s(td.total_seconds())


_TIMEDELTA_PREFIXES_RATIOS = [
    (60 * 60 * 24 * 7, 'w'),
    (60 * 60 * 24, 'd'),
    (60 * 60, 'h'),
    (60, 'm'),
    (1, 's'),
]


def format_timdelta_s(seconds: float) -> str:
    if seconds < 1e-3:
        return '0s'

    if seconds < 1:
        return f'{1000 * seconds:0.0f} ms'

    if seconds < 60:
        return f'{seconds:1.1f}s'

    seconds = round(seconds)
    parts: list[str] = []
    for part_seconds, part_name in _TIMEDELTA_PREFIXES_RATIOS:
        count = seconds // part_seconds
        if count > 0:
            seconds -= count * part_seconds
            parts.append(f'{count}{part_name}')

    return ' '.join(parts[:2])


@dataclasses.dataclass
class Timer:
    start: datetime.datetime = dataclasses.field(default_factory=datetime.datetime.now)
    _t0: float = dataclasses.field(init=False, default=0.0)
    _t1: float | None = dataclasses.field(init=False, default=None)

    @property
    def duration(self) -> datetime.timedelta:
        end = time.perf_counter() if self._t1 is None else self._t1
        return datetime.timedelta(seconds=end - self._t0)

    @property
    def formated_duration(self) -> str:
        return format_timdelta(self.duration)

    def __enter__(self) -> typing.Self:
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, *args: object) -> None:
        self._t1 = time.perf_counter()


# RETRY


class RetryTimeoutError(TimeoutError):
    def __init__(
        self,
        action: str,
        retry_count: int,
        duration: datetime.timedelta,
        errors: typing.Mapping[str, int],
    ) -> None:
        super().__init__(
            f'Timeout after retyring {action} {retry_count} times for {format_timdelta(duration)}'
        )
        for name, count in sorted(errors.items(), key=lambda t: t[1], reverse=True):
            self.add_note(f'Got {count} {name}')

        self.retry_count = retry_count
        self.duration = duration
        self.errors = errors


@dataclasses.dataclass(frozen=True, slots=True)
class RetryConfig:
    start_delay: datetime.timedelta
    max_delay: datetime.timedelta
    timeout: datetime.timedelta


@dataclasses.dataclass(frozen=True, slots=True)
class RetrySleep:
    duration: datetime.timedelta

    def sync(self) -> None:
        time.sleep(self.duration.total_seconds())

    async def asyncio(self) -> None:
        await asyncio.sleep(self.duration.total_seconds())


type GenericRetryErrorer[T, E] = typing.Callable[[T], E | None]


@dataclasses.dataclass(frozen=True, slots=True)
class GenericRetrier[T, E: typing.Hashable]:
    action: str
    config: RetryConfig
    timer: Timer
    errorer: GenericRetryErrorer[T, E]
    errors: collections.Counter[E]

    @staticmethod
    @contextlib.contextmanager
    def create(
        action: str, config: RetryConfig, errorer: GenericRetryErrorer[T, E]
    ) -> 'typing.Iterator[GenericRetrier[T, E]]':
        with Timer() as timer:
            yield GenericRetrier(
                action=action,
                config=config,
                timer=timer,
                errorer=errorer,
                errors=collections.Counter(),
            )

    def retry(self, value: T) -> T | RetrySleep:
        retry_count = sum(self.errors.values())
        error = self.errorer(value)

        if error is None:
            return value

        self.errors.update([error])

        if self.timer.duration > self.config.timeout:
            raise RetryTimeoutError(
                action=self.action,
                retry_count=retry_count,
                duration=self.timer.duration,
                errors={str(e): count for e, count in self.errors.items()},
            )

        delay = min(int(pow(2, retry_count)) * self.config.start_delay, self.config.max_delay)
        return RetrySleep(delay)


# MISC


def compute_sha256(data: bytes) -> str:
    return base64.b64encode(hashlib.sha256(data).digest()).decode('utf-8')
