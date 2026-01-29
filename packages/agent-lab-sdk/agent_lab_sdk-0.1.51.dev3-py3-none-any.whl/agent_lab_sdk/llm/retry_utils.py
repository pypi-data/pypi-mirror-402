from __future__ import annotations

from typing import Optional

from gigachat.exceptions import ResponseError
from pydantic import BaseModel, Field
import tenacity

_FORBIDDEN_EXCEPTION_MESSAGE = (
    "Произошло ограничение трафика на стороне GigaChat. "
    "Запрос не может быть выполнен. Попробуйте запустить агента позже."
)


def _retry_exception_predicate(exception: BaseException) -> bool:
    if isinstance(exception, ResponseError):
        status = exception.args[1]
        return status not in (401, 403)
    return True


def _retry_exception_transformer_sync(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ResponseError as exc:
            status = exc.args[1]
            if status in (401, 403):
                raise RuntimeError(_FORBIDDEN_EXCEPTION_MESSAGE) from exc
            raise

    return wrapper


def _retry_exception_transformer_async(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ResponseError as exc:
            status = exc.args[1]
            if status in (401, 403):
                raise RuntimeError(_FORBIDDEN_EXCEPTION_MESSAGE) from exc
            raise

    return wrapper


class RetryConfig(BaseModel):
    retry_attempts_count: int = Field(default=3, ge=0)
    wait_multiplier: float = Field(default=1, ge=0)
    wait_min: float = Field(default=0.5, ge=0)
    wait_max: float = Field(default=4, ge=0)


def normalize_retry_config(retry_config, retry_attempts_count=None) -> Optional[RetryConfig]:
    if retry_config is None:
        if retry_attempts_count is None:
            return None
        retry_config = {"retry_attempts_count": retry_attempts_count}
    if isinstance(retry_config, RetryConfig):
        return retry_config
    return RetryConfig.model_validate(retry_config)


def _retry_decorator(retry_config: RetryConfig):
    return tenacity.retry(
        retry=tenacity.retry_if_exception(_retry_exception_predicate),
        wait=tenacity.wait_exponential(
            multiplier=retry_config.wait_multiplier,
            min=retry_config.wait_min,
            max=retry_config.wait_max,
        ),
        stop=tenacity.stop_after_attempt(retry_config.retry_attempts_count),
        reraise=True,
    )


def _call_with_retry_sync(retry_config: RetryConfig, func):
    @_retry_exception_transformer_sync
    @_retry_decorator(retry_config)
    def call():
        return func()

    return call()


async def _call_with_retry_async(retry_config: RetryConfig, func):
    @_retry_exception_transformer_async
    @_retry_decorator(retry_config)
    async def call():
        return await func()

    return await call()


def maybe_retry_sync(
    retry_enabled: bool,
    retry_config: Optional[RetryConfig],
    func,
):
    if retry_enabled and retry_config and retry_config.retry_attempts_count > 0:
        return _call_with_retry_sync(retry_config, func)
    return func()


async def maybe_retry_async(
    retry_enabled: bool,
    retry_config: Optional[RetryConfig],
    func,
):
    if retry_enabled and retry_config and retry_config.retry_attempts_count > 0:
        return await _call_with_retry_async(retry_config, func)
    return await func()


__all__ = [
    "RetryConfig",
    "normalize_retry_config",
    "maybe_retry_sync",
    "maybe_retry_async",
]
