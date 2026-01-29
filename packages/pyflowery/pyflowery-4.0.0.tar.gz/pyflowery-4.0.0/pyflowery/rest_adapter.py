"""This module contains the RestAdapter class, which is used to make requests to the Flowery API."""

import email.utils
import time
from asyncio import sleep as asleep
from collections.abc import Mapping
from json import JSONDecodeError
from logging import Logger
from types import SimpleNamespace

from aiohttp import (
    ClientSession,
    ClientTimeout,
    ContentTypeError,
    TraceConfig,
    TraceRequestEndParams,
    TraceRequestExceptionParams,
    TraceRequestRedirectParams,
    TraceRequestStartParams,
)
from yarl import URL

from pyflowery.exceptions import (
    ClientError,
    InternalServerError,
    ResponseError,
    RetryableException,
    RetryLimitExceeded,
    TooManyRequests,
)
from pyflowery.models import FloweryAPIConfig, Result

__all__ = ["RestAdapter"]


def _sanitize_mapping(mapping: Mapping[str, str | float | int | bool]) -> dict[str, str]:
    """Sanitize a mapping by converting all values to strings.

    Args:
        mapping (Mapping[str, str | float | int | bool]): The mapping to sanitize.

    Returns:
        The sanitized dictionary.
    """
    return {k: str(v) for k, v in mapping.items()}


class RestAdapter:
    """Underlying class for making HTTP requests.

    Args:
        config (models.FloweryAPIConfig): Configuration object for the FloweryAPI class.
    """

    def __init__(self, config: FloweryAPIConfig) -> None:
        self.config: FloweryAPIConfig = config
        self._logger: Logger = self.config.logger.getChild("rest_adapter")
        self.session: ClientSession | None = None

    async def start(self) -> ClientSession:
        headers = {"User-Agent": self.config.prepended_user_agent}
        if self.config.token:
            headers["Authorization"] = f"Bearer {self.config.token}"

        if not self.config.base_url.endswith("/"):
            self.config.base_url += "/"

        self.session = ClientSession(
            base_url=self.config.base_url,
            headers=headers,
            trace_configs=[self._trace_config()],
        )
        return self.session

    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()

    def _trace_config(self) -> TraceConfig:
        trace_config = TraceConfig()
        trace_config.on_request_start.append(self._on_request_start)
        trace_config.on_request_redirect.append(self._on_request_redirect)
        trace_config.on_request_end.append(self._on_request_end)
        trace_config.on_request_exception.append(self._on_request_exception)
        return trace_config

    @staticmethod
    def _trace_get_duration(end_time: float, trace_config_ctx: SimpleNamespace) -> str:
        start_time = getattr(trace_config_ctx, "start_time", None)
        if isinstance(start_time, float):
            return f"request took approximately {end_time - start_time:.4f}s"
        return "failed to get request duration"

    @staticmethod
    def _trace_get_urls(end_url: URL, trace_config_ctx: SimpleNamespace) -> str:
        urls = getattr(trace_config_ctx, "urls", [])
        if not isinstance(urls, list) or len(urls) <= 1:  # pyright: ignore[reportUnknownArgumentType]
            return f"'{end_url}'"

        redirect_chain = [f"'{url}'" for url in urls[:-1]]  # pyright: ignore[reportUnknownVariableType]

        full_chain = redirect_chain + [f"'{end_url}'"]

        return " >> ".join(full_chain)

    @staticmethod
    async def _on_request_start(
        session: ClientSession,  # pyright: ignore[reportUnusedParameter]
        trace_config_ctx: SimpleNamespace,
        params: TraceRequestStartParams,
    ) -> None:
        trace_config_ctx.start_time = time.monotonic()
        trace_config_ctx.urls = [params.url]

    @staticmethod
    async def _on_request_redirect(
        session: ClientSession,  # pyright: ignore[reportUnusedParameter]
        trace_config_ctx: SimpleNamespace,
        params: TraceRequestRedirectParams,
    ) -> None:
        redirect_target = params.response.headers.get("Location", None)
        if redirect_target:
            redirect_target = URL(redirect_target)
            urls = getattr(trace_config_ctx, "urls", None)
            if not isinstance(urls, list):
                trace_config_ctx.urls = [params.url, redirect_target]
                return
            urls.append(redirect_target)  # pyright: ignore[reportUnknownMemberType]
            trace_config_ctx.urls = urls

    async def _on_request_end(
        self,
        session: ClientSession,  # pyright: ignore[reportUnusedParameter]
        trace_config_ctx: SimpleNamespace,
        params: TraceRequestEndParams,
    ) -> None:
        end_time = time.monotonic()
        url = self._trace_get_urls(params.url, trace_config_ctx)

        message: str | None = None
        if params.response.status >= 400:
            try:
                data = await params.response.json()  # pyright: ignore[reportAny]
                message = str(data["error"])  # pyright: ignore[reportAny]
            except Exception:
                pass

        self._logger.debug(
            "%s %s -> %s %s%s (%s)",
            params.method,
            url,
            params.response.status,
            params.response.reason,
            f": {message}" if message else "",
            self._trace_get_duration(end_time, trace_config_ctx),
        )

    async def _on_request_exception(
        self,
        session: ClientSession,  # pyright: ignore[reportUnusedParameter]
        trace_config_ctx: SimpleNamespace,
        params: TraceRequestExceptionParams,
    ) -> None:
        end_time = time.monotonic()
        url = self._trace_get_urls(params.url, trace_config_ctx)
        self._logger.error(
            "%s request to %s encountered an exception (%s)",
            params.method,
            url,
            self._trace_get_duration(end_time, trace_config_ctx),
            exc_info=params.exception,
        )

    async def _do(
        self,
        http_method: str,
        endpoint: str,
        data: str | None = None,
        headers: Mapping[str, str | float | int | bool] | None = None,
        params: Mapping[str, str | float | int | bool] | None = None,
        timeout: float = 60,
    ) -> Result:
        """Internal method to make a request to the Flowery API. You shouldn't use this directly.

        If you need to use this method because an endpoint is missing, please open an issue on the [CoastalCommits repository](https://c.csw.im/cswimr/PyFlowery/issues).

        Args:
            http_method (str): The [HTTP method](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods) to use.
            endpoint (str): The endpoint to make the request to.
            data (str | None): The request body.
            headers (Mapping[str, str | float | int | bool] | None): Headers to send with the request. Note that `User-Agent` and `Authorization` headers will be overridden by the library if provided.
            params (Mapping[str, str | float | int | bool] | None): Query parameters to send with the request.
            timeout (float): Number of seconds to wait for the request to complete.

        Raises:
            exceptions.TooManyRequests: Raised when the Flowery API returns a 429 status code
            exceptions.ClientError: Raised when the Flowery API returns a 4xx status code
            exceptions.InternalServerError: Raised when the Flowery API returns a 5xx status code
            exceptions.RetryLimitExceeded: Raised when the retry limit defined in the [`FloweryAPIConfig`][models.FloweryAPIConfig] class (default 3) is exceeded

        Returns:
            Result: A Result object containing the status code, message, and data from the request.
        """
        if not self.session:
            self.session = await self.start()
        elif self.session and self.session.loop.is_closed():
            try:
                _ = await self.session.close()
            except Exception:
                pass
            self.session = await self.start()

        full_url = self.config.base_url + endpoint

        sanitized_headers = _sanitize_mapping(headers) if headers else {}
        sanitized_headers.update(
            {
                "User-Agent": self.config.prepended_user_agent,
            }
        )

        sanitized_params = _sanitize_mapping(params) if params else {}
        retry_counter = 0

        while retry_counter <= self.config.retry_limit:
            async with self.session.request(
                method=http_method,
                url=full_url,
                data=data,
                params=sanitized_params,
                headers=sanitized_headers,
                timeout=ClientTimeout(timeout),
            ) as response:
                try:
                    _data = await response.json()  # pyright: ignore[reportAny]
                except (JSONDecodeError, ContentTypeError):
                    _data = await response.read()

                cache_hit = None
                if raw_cache_hit := response.headers.get("X-Cache-Status", None):
                    cache_hit = True if raw_cache_hit == "HIT" else False

                cache_expires = None
                if raw_cache_expires := response.headers.get("Expires", None):
                    cache_expires = email.utils.parsedate_to_datetime(raw_cache_expires)

                result = Result(
                    success=response.status <= 400,
                    status_code=response.status,
                    message=response.reason or "Unknown error",
                    data=_data,
                    cache_hit=cache_hit,
                    cache_expires=cache_expires,
                    raw_response=response,
                )

                try:
                    if result.status_code == 429:
                        raise TooManyRequests(str(result), result)
                    if 400 <= result.status_code < 500:
                        raise ClientError(str(result), result)
                    if 500 <= result.status_code < 600:
                        raise InternalServerError(str(result), result)
                except RetryableException as e:
                    if self.config.retry_limit <= 0:
                        raise e
                    if retry_counter < self.config.retry_limit:
                        interval = self.config.interval * retry_counter
                        self._logger.exception("%s - retrying in %s seconds", e, interval)
                        retry_counter += 1
                        await asleep(interval)
                        continue
                    raise RetryLimitExceeded(
                        message=f"Request failed more than {self.config.retry_limit} times, not retrying.", result=result
                    ) from e
                return result
        # this shouldn't ever happen but is here to keep typecheckers happy
        message = "Empty Response! Something went wrong in RestAdapter!"
        raise ResponseError(
            message,
            Result(success=False, status_code=400, message=message),
        )

    async def get(
        self,
        endpoint: str,
        data: str | None = None,
        headers: Mapping[str, str | float | int | bool] | None = None,
        params: Mapping[str, str | float | int | bool] | None = None,
        timeout: float = 60,
    ) -> Result:
        """Make a GET request to the Flowery API. You should almost never have to use this directly.

        If you need to use this method because an endpoint is missing, please open an issue on the [CoastalCommits repository](https://c.csw.im/cswimr/PyFlowery/issues).

        Args:
            endpoint (str): The endpoint to make the request to.
            data (str | None): The request body.
            headers (Mapping[str, str | float | int | bool] | None): Headers to send with the request. Note that `User-Agent` and `Authorization` headers will be overridden by the library if provided.
            params (Mapping[str, str | float | int | bool] | None): Query parameters to send with the request.
            timeout (float): Number of seconds to wait for the request to complete.

        Raises:
            exceptions.TooManyRequests: Raised when the Flowery API returns a 429 status code
            exceptions.ClientError: Raised when the Flowery API returns a 4xx status code
            exceptions.InternalServerError: Raised when the Flowery API returns a 5xx status code
            exceptions.RetryLimitExceeded: Raised when the retry limit defined in the [`FloweryAPIConfig`][models.FloweryAPIConfig] class (default 3) is exceeded

        Returns:
            An object containing the status code, message, and data from the request.
        """
        return await self._do(http_method="GET", endpoint=endpoint, data=data, headers=headers, params=params, timeout=timeout)

    async def post(
        self,
        endpoint: str,
        data: str | None = None,
        headers: Mapping[str, str | float | int | bool] | None = None,
        params: Mapping[str, str | float | int | bool] | None = None,
        timeout: float = 60,
    ) -> Result:
        """Make a POST request to the Flowery API. You should almost never have to use this directly.

        If you need to use this method because an endpoint is missing, please open an issue on the [CoastalCommits repository](https://c.csw.im/cswimr/PyFlowery/issues).

        Args:
            endpoint (str): The endpoint to make the request to.
            data (str | None): The request body.
            headers (Mapping[str, str | float | int | bool] | None): Headers to send with the request. Note that `User-Agent` and `Authorization` headers will be overridden by the library if provided.
            params (Mapping[str, str | float | int | bool] | None): Query parameters to send with the request.
            timeout (float): Number of seconds to wait for the request to complete.

        Raises:
            exceptions.TooManyRequests: Raised when the Flowery API returns a 429 status code
            exceptions.ClientError: Raised when the Flowery API returns a 4xx status code
            exceptions.InternalServerError: Raised when the Flowery API returns a 5xx status code
            exceptions.RetryLimitExceeded: Raised when the retry limit defined in the [`FloweryAPIConfig`][models.FloweryAPIConfig] class (default 3) is exceeded

        Returns:
            An object containing the status code, message, and data from the request.
        """
        return await self._do(http_method="POST", endpoint=endpoint, data=data, headers=headers, params=params, timeout=timeout)
