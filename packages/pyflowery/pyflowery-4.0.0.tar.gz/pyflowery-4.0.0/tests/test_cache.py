from pyflowery import FloweryAPI
from pyflowery.utils import call_async

from .config import config

api = FloweryAPI(config)


def test_cache_population():
    assert len(api._voices_cache) == 0  # pyright: ignore[reportPrivateUsage]
    _ = call_async(api.fetch_voices(), api.logger)
    assert len(api._voices_cache) > 0  # pyright: ignore[reportPrivateUsage]
    _ = call_async(api.close(), api.logger)
