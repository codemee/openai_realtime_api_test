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
    last_audio_item_id = None

    async with client.beta.realtime.connect(
        model="gpt-4o-realtime-preview",
        # 可以透過 extra_query 傳遞額外的引數
        extra_query = {"voice": "alloy"},
    ) as conn:
        connection = conn
        # 建立交談階段後還可以修改設定
        # await conn.session.update(
        #     session={
        #         # 伺服端預設就會採用 VAD（Voice Activation Detection）
        #         # 自動偵測開始講話與結束，若改成 'turn_detection': None，
        #         # 就要手動在講話結束時提交音訊資料
        #         "turn_detection": {"type": "server_vad"},
        #         # 雖然 input_audio_transcription 的所有參數都是 optional，
        #         # 但是若傳空的物件，雖然可以建立連線，但是開始傳送語音就會出錯
        #         "input_audio_transcription": {"model": "whisper-1"},
        #         "voice": "alloy",
        #     }
        # )

        acc_items: dict[str, Any] = {}

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
                    if event.item_id != last_audio_item_id:
                        audio_player.reset_frame_count()
                        last_audio_item_id = event.item_id

                    bytes_data = base64.b64decode(event.delta)
                    audio_player.add_data(bytes_data)
                    continue
                
                # 如果使用者有講新的話，就停止播放音訊，避免新對話的文字回應送來了
                # 但之前的語音回覆還在繼續播放
                if event.type == "input_audio_buffer.speech_started":
                    audio_player.stop()
                    continue

                # 回應內容的文字是用串流方式一段一段送回來
                if event.type == "response.audio_transcript.delta":
                    try:
                        text = acc_items[event.item_id]
                    except KeyError: # 第一次收到文字回應的片段
                        acc_items[event.item_id] = event.delta
                    else: # 累加之後收到的文字回應片段
                        acc_items[event.item_id] = text + event.delta

                    # 清除顯示區域重新顯示累加的回應內容才能呈現串流的效果
                    # print(f"\r{acc_items[event.item_id]}", flush = True, end="")
                    continue
                
                # 當回應內容的文字送完了，就印出來
                if event.type == "response.audio_transcript.done":
                    # print(f"{acc_items[event.item_id]}")
                    print(event.transcript)
                    del acc_items[event.item_id]
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

            # 傳送音訊資料給伺服端，伺服端會自動判斷段落就回應
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
    # should_send_audio.set()
    is_recording = False
    while True:
        keys = getkeys()
        if len(keys) == 0:            
            await asyncio.sleep(0)
            continue
        key = keys.pop().lower()
        if key == "k":
            is_recording = not is_recording
            if is_recording:
                should_send_audio.set()
            else:
                should_send_audio.clear()
        elif key == "q":
            break
        await asyncio.sleep(0)
    mic_task.cancel()
    realtime_task.cancel()
    await asyncio.gather(mic_task, realtime_task)
if __name__ == "__main__":
    asyncio.run(main())
