import sys
from datetime import datetime
from enum import StrEnum
from logging import INFO, Formatter, Logger, StreamHandler, getLogger
from typing import Any, ClassVar, Self

import aiohttp
from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import override

from pyflowery.version import version

__all__ = ["Result", "AudioFormat", "Voice", "Language", "TTSResponse", "FloweryAPIConfig"]


class Result(BaseModel):
    """Result returned from low-level RestAdapter."""

    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    success: bool
    """Whether or not the request was successful."""
    status_code: int
    """The [HTTP status code](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status) returned by the request."""
    message: str = ""
    """Human readable result message from the request."""
    data: list[dict[str, Any]] | dict[str, Any] | bytes = {}  # pyright: ignore[reportExplicitAny]
    """The data returned by the request."""
    cache_hit: bool | None = None
    """Whether or not the data in this result was returned via a cache from the external API.

    Will be `None` in cases where the external API does not tell us if the result was cached.
    """
    cache_expires: datetime | None = None
    """The timestamp at which the data in this result will expire, if it was cached by the external API.

    Will be `None` in cases where the external API does not tell us if the result was cached.
    """
    raw_response: aiohttp.ClientResponse | None = None
    """The raw response object from the request."""

    @override
    def __str__(self) -> str:
        message = self.message
        if not self.success:
            if isinstance(self.data, dict) and (error := self.data.get("error")):
                message = f"{message}: {error}"
        if self.cache_hit is not None:
            return f"{self.status_code} {message} (Cache {'hit' if self.cache_hit else 'miss'})"
        return f"{self.status_code} {message}"


class AudioFormat(StrEnum):
    """List of audio formats accepted by Flowery."""

    MP3 = "audio/mpeg"
    """[MP3](https://en.wikipedia.org/wiki/MP3) audio format."""
    OPUS = "audio/ogg; codecs=opus"
    """[OGG](https://en.wikipedia.org/wiki/Ogg) [Opus](https://en.wikipedia.org/wiki/Opus_(audio_format)) audio format."""
    VORBIS = "audio/ogg; codecs=vorbis"
    """[OGG](https://en.wikipedia.org/wiki/Ogg) [Vorbis](https://en.wikipedia.org/wiki/Vorbis) audio format."""
    AAC = "audio/x-aac"
    """[AAC](https://en.wikipedia.org/wiki/Advanced_Audio_Coding) audio format."""
    WAV = "audio/wav"
    """[WAV](https://en.wikipedia.org/wiki/WAV) audio format."""
    FLAC = "audio/x-flac"
    """[FLAC](https://en.wikipedia.org/wiki/FLAC) audio format."""


class Language(BaseModel):
    """Language object returned from the Flowery API."""

    name: str | None = None
    """The name associated with the language."""
    code: str
    """The code associated with the language."""

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Language):
            return True if self.code == other.code else False
        return False

    @classmethod
    def english(cls) -> list[Self]:
        return [
            cls(code="en-US", name="English (United States)"),
            cls(code="en_US", name="English (United States)"),
            cls(code="en-GB", name="English (Great Britain)"),
            cls(code="en_GB", name="English (Great Britain)"),
            cls(code="en", name="English"),
        ]


class Voice(BaseModel):
    """Voice object returned from the Flowery API."""

    id: str
    """UUID of the voice."""
    name: str
    """Name of the voice."""
    gender: str
    """Gender of the voice."""
    source: str
    """Which provider the voice comes from."""
    language: Language
    """Which language the voice is meant to be used for."""


class TTSResponse(BaseModel):
    """Object containing data from a TTS query."""

    data: bytes
    """The synthesized TTS data in bytes."""
    text: str
    """The SSML text used to generate the TTS data."""
    voice: Voice | None = None
    """Whether the text was translated into the voice's set language before being synthesized."""
    audio_format: AudioFormat
    """What format the data is in."""
    result: Result
    """The internal result object for use in debugging."""


def _create_logger(level: str | int = INFO) -> Logger:
    """Creates a logger for the library."""
    logger = getLogger("pyflowery")
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    handler = StreamHandler(sys.stderr)
    handler.setLevel(level)

    formatter = Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


class FloweryAPIConfig(BaseModel):
    """Configuration used when making requests to the Flowery API.

    Example:
        ```python
        from pyflowery import FloweryAPI, FloweryAPIConfig

        config = FloweryAPIConfig(
            user_agent = "PyFloweryDocumentation/1.0.0",
            token = "hello world",
        )

        api = FloweryAPI(config=config)
        ```
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True, validate_default=True)

    user_agent: str
    """User-Agent string to use in HTTP requests. Required as of 2.1.0."""
    token: str | None = None
    """Authorization token to use in HTTP requests. Authorization is only required if you want increased ratelimits.
            See the [Flowery API documentation](https://flowery.pw/docs) for more details."""
    base_url: str = "https://api.flowery.pw/v2"
    """The base url for the Flowery API."""
    logger: Logger = Field(default_factory=_create_logger)
    """Logger to use for logging messages. One will be automatically created if not provided here."""
    retry_limit: int = 3
    """Number of times to retry a request before giving up."""
    interval: int = 5
    """Seconds to wait between each retried request, multiplied by how many attempted requests have been made."""

    @property
    def prepended_user_agent(self) -> str:
        """Return the user_agent with the PyFlowery module version prepended."""
        return f"PyFlowery/{version} {self.user_agent} (Python {sys.version})"
