import asyncio
from collections.abc import Mapping
from copy import deepcopy
from logging import Logger
from typing import overload

from lxml import etree
from pydantic import ValidationError

from pyflowery import exceptions, models, rest_adapter, utils

__all__ = ["FloweryAPI"]


class FloweryAPI:
    """Main class for interacting with the Flowery API.

    Example:
        ```python
        from pyflowery import FloweryAPI, FloweryAPIConfig

        config = FloweryAPIConfig(
            user_agent = "PyFloweryDocumentation/1.0.0",
            token = "hello world",
            allow_truncation = False,
        )

        api = FloweryAPI(config=config)
        ```
    """

    def __init__(self, config: models.FloweryAPIConfig) -> None:
        self.config: models.FloweryAPIConfig = config
        """Object for configuring requests to the Flowery API."""
        self.adapter: rest_adapter.RestAdapter = rest_adapter.RestAdapter(config=config)
        """Rest Adapter used for making HTTP requests."""
        self.logger: Logger = self.config.logger
        """The logger used internally."""

        self._voices_cache: Mapping[str, models.Voice] = {}
        self._voices_populating: asyncio.Task[Mapping[str, models.Voice]] | None = None

    async def close(self) -> None:
        """Close the currently open client session."""
        await self.adapter.close()

    def _ensure_voices_cache(self) -> None:
        if self._voices_cache:
            return
        _ = utils.call_async(self.fetch_voices(), self.logger)

    def get_voice(self, voice_id: str) -> models.Voice | None:
        """Get a voice from the cache using its ID.

        Example:
            ```python
            from pyflowery import FloweryAPI, FloweryAPIConfig

            api = FloweryAPI(config=FloweryAPIConfig(user_agent="PyFloweryDocumentation/1.0.0"))
            voice = api.get_voice("372a5e97-1645-563a-9097-36bd83184ab4")
            # Voice(
            #   id='372a5e97-1645-563a-9097-36bd83184ab4',
            #   name='Xiaoyi', gender='Female', source='Microsoft Azure',
            #   language=Language(name='Chinese (China)', code='zh-CN')
            # )
            ```

        Args:
            voice_id (str): The ID of the voice to retrieve from the cache.

        Returns:
            The matching [`Voice`][models.Voice] if found, otherwise `None`.
        """
        self._ensure_voices_cache()
        return self._voices_cache.get(voice_id.lower())

    @overload
    def get_voices(self) -> tuple[models.Voice, ...]: ...

    @overload
    def get_voices(
        self,
        *,
        name: str | None = None,
        gender: str | None = None,
        source: str | None = None,
        languages: list[models.Language] | models.Language | None = None,
    ) -> tuple[models.Voice, ...] | None: ...

    def get_voices(
        self,
        *,
        name: str | None = None,
        gender: str | None = None,
        source: str | None = None,
        languages: list[models.Language] | models.Language | None = None,
    ) -> tuple[models.Voice, ...] | None:
        """Get a filtered set of voices from the cache.

        Example:
            ```python
            from pyflowery import FloweryAPI, FloweryAPIConfig, Language

            api = FloweryAPI(config=FloweryAPIConfig(user_agent="PyFloweryDocumentation/1.0.0"))
            voices = api.get_voices(source="TikTok", languages=Language(name="English (United States)", code="en-US"))
            # (
            #   Voice(
            #       id='fa3ea565-121f-5efd-b4e9-59895c77df23',
            #       name='Alexander', gender='Male', source='TikTok',
            #       language=Language(name='English (United States)', code='en-US')
            #   ),
            #   Voice(
            #       id='a55b0ad0-84c8-597d-832b-0bc4c8777054',
            #       name='Alto', gender='Female', source='TikTok',
            #       language=Language(name='English (United States)', code='en-US')
            #   ), ...
            ```

        Args:
            name: The name to filter results by.
            gender: The gender to filter results by.
            source: The source to filter results by.
            languages: The languages to filter results by.

        Returns:
            (tuple[models.Voice, ...]): All voices when no filters are given.
            (tuple[models.Voice, ...] | None): Filtered voices (or None if no matches).
        """
        self._ensure_voices_cache()

        if not any([name, gender, source, languages]):
            return tuple(self._voices_cache.values())

        if languages and not isinstance(languages, list):
            languages = [languages]

        language_codes = {lang.code for lang in languages} if languages else None

        voices: list[models.Voice] = []

        for voice in self._voices_cache.values():
            if name is not None and voice.name.lower() != name.lower():
                continue
            if gender is not None and voice.gender.lower() != gender.lower():
                continue
            if source is not None and voice.source.lower() != source.lower():
                continue
            if language_codes is not None and voice.language.code not in language_codes:
                continue
            voices.append(voice)

        return tuple(voices) if len(voices) > 0 else None

    async def fetch_voices(self) -> Mapping[str, models.Voice]:
        """Fetch a mapping of voice IDs to voices from the Flowery API.

        Calling this method will repopulate the built-in voices cache.

        Raises:
            exceptions.TooManyRequests: Raised when the Flowery API returns a 429 status code.
            exceptions.ClientError: Raised when the Flowery API returns a 4xx status code.
            exceptions.InternalServerError: Raised when the Flowery API returns a 5xx status code.
            exceptions.ResponseError: Raised when the Flowery API returns an empty response or a response with an unexpected format.
            exceptions.RetryLimitExceeded: Raised when the retry limit defined in the `FloweryAPIConfig` class (default 3) is exceeded.

        Returns:
            A mapping of voice IDs to voices.
        """
        request = await self.adapter.get(endpoint="voices")
        if request.success is not True or not isinstance(request.data, dict):
            raise exceptions.ResponseError(f"Invalid response from Flowery API: {request.data!r}", request)

        data: list[dict[str, str]] = request.data.get("voices", [])  # pyright: ignore[reportAny]
        voices: dict[str, models.Voice] = {}
        for voice in data:
            try:
                v = models.Voice.model_validate(voice)
                voices[v.id.lower()] = v
            except ValidationError as e:
                self.config.logger.exception("Failed to validate voice data. Voice Data: %s, Error: %s", voice, str(e))
                continue
        self._voices_cache = deepcopy(voices)
        self.logger.debug("Voices cache populated with %d entries!", len(self._voices_cache))
        return voices

    async def fetch_tts(
        self,
        text: str | etree._Element,  # pyright: ignore[reportPrivateUsage]
        voice: models.Voice,
        audio_format: models.AudioFormat = models.AudioFormat.MP3,
        speed: float = 1.0,
    ) -> models.TTSResponse:
        """Fetch a TTS audio file from the Flowery API.

        Args:
            text (str | lxml.etree._Element): The SSML text to convert to speech. This will be contained within the body of a `<voice>` tag.
                See the [Flowery SSML documentation](https://flowery.pw/docs/ssml) for more information on SSML.
            voice (models.Voice): The voice to use for the speech.
            audio_format (models.AudioFormat): The audio format to return.

        Raises:
            ValueError: Raised when the provided text is too long.
            exceptions.TooManyRequests: Raised when the Flowery API returns a 429 status code.
            exceptions.ClientError: Raised when the Flowery API returns a 4xx status code.
            exceptions.InternalServerError: Raised when the Flowery API returns a 5xx status code.
            exceptions.ResponseError: Raised when the Flowery API returns an empty response or a response with an unexpected format.
            exceptions.RetryLimitExceeded: Raised when the retry limit defined in the [`FloweryAPIConfig`][models.FloweryAPIConfig] class (default 3) is exceeded.

        Returns:
            An object containing the parameters used to synthesize the text, as well as the raw tts data in bytes.
        """
        if len(text) > 4096:
            raise ValueError("Text must be less than or equal to 4096 characters")

        headers = {"Content-Type": "application/xml; charset=UTF-8", "Accept": audio_format}

        speak = etree.Element("speak")
        ssml_voice = etree.SubElement(speak, "voice", name=voice.id)
        if isinstance(text, str):
            try:
                ssml_voice.append(etree.fromstring(text))
            except etree.XMLSyntaxError:
                ssml_voice.text = text
        else:
            ssml_voice.append(text)

        body = etree.tostring(speak, pretty_print=True).decode()

        params = {
            "text": text,
            "audio_format": audio_format,
            "speed": speed,
        }
        if voice:
            params["voice"] = voice.id

        request = await self.adapter.post(endpoint="tts", headers=headers, data=body, timeout=180)

        if isinstance(request.data, bytes):
            return models.TTSResponse(data=request.data, text=body, voice=voice, audio_format=audio_format, result=request)
        raise exceptions.ResponseError(f"Invalid response from Flowery API: {request.data!r}", request)
