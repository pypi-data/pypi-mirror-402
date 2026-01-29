from datetime import timedelta
from random import choice
from typing import TypeAlias

import pytest
from pydantic import ValidationError

from pyflowery import AudioFormat, FloweryAPI, Result, TTSResponse, Voice
from pyflowery.utils import call_async

from ..config import config

api = FloweryAPI(config)


class TestTTSResponse:
    # Sample data for testing
    sample_voice: Voice = choice(api.get_voices())
    sample_audio_format: AudioFormat = choice(tuple(AudioFormat))

    T: TypeAlias = dict[str, bytes | str | Voice | bool | timedelta | AudioFormat | Result | float]

    @pytest.fixture
    def valid_data(self) -> T:
        return {
            "data": b"audio_data",
            "text": "Hello world",
            "voice": self.sample_voice,
            "audio_format": self.sample_audio_format,
            "result": Result(success=True, status_code=200),
        }

    def test_valid_model_creation(self, valid_data: T):
        """Test that a model can be created with valid data"""
        response = TTSResponse.model_validate(valid_data)

        assert response.data == valid_data["data"]
        assert response.text == valid_data["text"]
        assert response.voice == valid_data["voice"]
        assert response.audio_format == valid_data["audio_format"]
        assert response.result == valid_data["result"]

    def test_required_fields(self, valid_data: T):
        """Test that required fields are enforced"""
        required_fields = ["data", "text", "audio_format", "result"]

        for field in required_fields:
            data = valid_data.copy()
            _ = data.pop(field)
            with pytest.raises(ValidationError):
                _ = TTSResponse.model_validate(data)

    def test_default_values(self, valid_data: T):
        """Test default values are set correctly"""
        data = {"data": b"audio", "text": "text", "audio_format": self.sample_audio_format, "result": valid_data["result"]}

        response = TTSResponse.model_validate(data)

        assert response.voice is None


_ = call_async(api.close(), config.logger)
