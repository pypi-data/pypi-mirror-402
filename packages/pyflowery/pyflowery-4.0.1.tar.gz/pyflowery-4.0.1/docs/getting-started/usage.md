# Usage

This page contains a few examples of how to use the `pyflowery` package. This page does not cover installation, for that see the [installation](installation.md) page.

## Creating an API client

To create an API client, you need to first import the `pyflowery.pyflowery.FloweryAPI` class. Then, you can create an instance of the class by passing in a `pyflowery.models.FloweryAPIConfig` class.

```python
from pyflowery import FloweryAPI, FloweryAPIConfig
config = FloweryAPIConfig(user_agent="PyFlowery Documentation Example/example@foobar.com")
api = FloweryAPI(config)
```

Okay, now we have a `FloweryAPI` class. Let's move on to the next example.

## Retrieving a voice

Whenever `get_voices` or `get_voice` is called for the first time, it will automatically try to populate the voices cache by querying Flowery's API. If you are using the library in an async context and don't want this to block, call `await api.fetch_voices()` first. This will populate the cache without blocking the rest of the thread.

```python
# Set up the API client
from pyflowery import FloweryAPI, FloweryAPIConfig
config = FloweryAPIConfig(user_agent="PyFlowery Documentation Example/example@foobar.com")
api = FloweryAPI(config)

# This will fetch all of the voices from the API and cache them to speed up repeated queries.
voices = api.get_voices(name="Alexander")
print(voices) # (Voice(id='fa3ea565-121f-5efd-b4e9-59895c77df23', name='Alexander', gender='Male', source='TikTok', language=Language(name='English (United States)', code='en-US')),)
print(voices[0].id) # 'fa3ea565-121f-5efd-b4e9-59895c77df23'
```

## Retrieving a list of voices from the API directly

If necessary, you can call the `fetch_voices()` method. This method will fetch the voices from the API directly, skipping the cache. This isn't recommended, though, as it puts more strain on the Flowery API. Do note that using this method will also update the built-in voices cache.

```python
import asyncio
from pyflowery import FloweryAPI, FloweryAPIConfig
config = FloweryAPIConfig(user_agent="PyFlowery Documentation Example/example@foobar.com")
api = FloweryAPI(config)

voices = asyncio.run(api.fetch_voices())
print(voices)
# {"fa3ea565-121f-5efd-b4e9-59895c77df23": Voice(id='fa3ea565-121f-5efd-b4e9-59895c77df23', name='Alexander', gender='Male', source='TikTok', language=Language(name='English (United States)', code='en-US')), ...}
```

## Converting text to audio

Finally, let's convert some text into audio. To do this, you can call the `fetch_tts()` method. This will return the bytes of the audio file.

```python
import asyncio
from pyflowery import FloweryAPI, FloweryAPIConfig
config = FloweryAPIConfig(user_agent="PyFlowery Documentation Example/example@foobar.com")
api = FloweryAPI(config)

voice = api.get_voices(name="Alexander")[0]

tts = asyncio.run(api.fetch_tts("Hello, world!", voice))
with open("hello_world.mp3", "wb") as f:
    f.write(tts)
```
