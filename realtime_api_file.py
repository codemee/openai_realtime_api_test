from audio_util import audio_to_pcm16_base64, AudioPlayerAsync
import asyncio
import base64
from openai import AsyncOpenAI

audio_player: AudioPlayerAsync = AudioPlayerAsync()

f = open("chinese.mp3", "rb")
audio = f.read()
f.close()

audio = audio_to_pcm16_base64(audio)

async def main():
    client = AsyncOpenAI()

    async with client.beta.realtime.connect(model="gpt-4o-realtime-preview") as connection:
        # await connection.session.update(session={'modalities': ['text']})

        await connection.conversation.item.create(
            item={
                "type": "message",
                "role": "user",
                "content": [{"type": "input_audio", "audio": audio}],
            }
        )
        await connection.response.create()

        async for event in connection:
            print(event.type)
            if event.type == "response.audio.delta":
                bytes_data = base64.b64decode(event.delta)
                audio_player.add_data(bytes_data)
                continue

            if event.type == 'response.audio_transcript.done':
                print(event.transcript)
                continue

            if event.type == 'response.text.done':
                print(event.text)
                continue
            
            if event.type == 'response.done':
                break

asyncio.run(main())