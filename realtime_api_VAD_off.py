from __future__ import annotations

import base64
import asyncio
from typing import Any, cast
from typing_extensions import override

from audio_util import CHANNELS, SAMPLE_RATE, AudioPlayerAsync

from openai import AsyncOpenAI
from openai.types.beta.realtime.session import Session
from openai.resources.beta.realtime.realtime import AsyncRealtimeConnection

from getchar import getkeys

connection: AsyncRealtimeConnection | None = None
audio_player: AudioPlayerAsync = AudioPlayerAsync()
should_send_audio: asyncio.Event = asyncio.Event()
connected: asyncio.Event = asyncio.Event()

async def handle_realtime_connection() -> None:
    global connection
    session: Session | None = None

    client: AsyncOpenAI = AsyncOpenAI()

    async with client.beta.realtime.connect(
        model="gpt-4o-realtime-preview",
        # 可以透過 extra_query 傳遞額外的引數
        extra_query = {"voice": "alloy"},
    ) as conn:
        connection = conn
        # 建立交談階段後還可以修改設定
        await conn.session.update(
            session={"turn_detection": None}
        )

        try:
            async for event in conn:
                print(f'{event.type}:id('
                      f'{event.item.id if hasattr(event, "item") else ""}'
                      f'{event.item_id if hasattr(event, "item_id") else ""})')
                if event.type == "session.created":
                    session = event.session
                    connected.set()
                    continue

                if event.type == "session.updated":
                    session = event.session
                    continue

                # 回應內容的語音也是一段一段送來
                if event.type == "response.audio.delta":
                    bytes_data = base64.b64decode(event.delta)
                    audio_player.add_data(bytes_data)
                    continue
                                
                # 回應內容的文字是用串流方式一段一段送回來
                if event.type == "response.audio_transcript.delta":
                    continue
                
                # 當回應內容的文字送完了，就印出來
                if event.type == "response.audio_transcript.done":
                    print(event.transcript)
                    continue

                if event.type == "error":
                    print(event.error.message)
                    continue

        except asyncio.CancelledError:
            pass

async def send_mic_audio() -> None:
    global connection
    import sounddevice as sd  # type: ignore

    sent_audio = False

    read_size = int(SAMPLE_RATE * 0.02)

    stream = sd.InputStream(
        channels=CHANNELS,
        samplerate=SAMPLE_RATE,
        dtype="int16",
    )
    stream.start()

    try:
        while True:
            # 先累積基本的音訊資料
            if stream.read_available < read_size:
                await asyncio.sleep(0)
                continue

            # 等待按下 K 鍵才開始傳送音訊資料
            await should_send_audio.wait()

            data, _ = stream.read(read_size)

            # 傳送音訊資料給伺服端
            await connection.input_audio_buffer.append(
                audio=base64.b64encode(cast(Any, data)).decode("utf-8")
            )
            await asyncio.sleep(0)
    except KeyboardInterrupt:
        pass
    except asyncio.CancelledError:
        pass
    finally:
        stream.stop()
        stream.close()


async def main() -> None:
    mic_task = asyncio.create_task(send_mic_audio())
    realtime_task = asyncio.create_task(handle_realtime_connection())

    await connected.wait()

    is_recording = False
    while True:
        keys = getkeys()
        if len(keys) == 0: 
            # 請特別留意，如果設為等待 0 秒，就會發生頻繁插斷語音播放造成顫音
            await asyncio.sleep(0.01)
            continue
        key = keys.pop().lower()
        if key == "k":
            is_recording = not is_recording
            if is_recording:
                should_send_audio.set()
            else:
                should_send_audio.clear()
                # 停止播放回覆語音
                audio_player.stop()
                # 由於關閉 VAD，所以要手動提交語音並且指示伺服端生成回應
                await connection.input_audio_buffer.commit()
                await connection.response.create()
        elif key == "q":
            break

    mic_task.cancel()
    realtime_task.cancel()
    await asyncio.gather(mic_task, realtime_task)
if __name__ == "__main__":
    asyncio.run(main())
