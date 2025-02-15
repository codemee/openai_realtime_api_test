import asyncio
from openai import AsyncOpenAI
from rich.pretty import pprint
from search_tools import google_res, GoogleRes

tools = [{
    "type":"function",
    # 注意 Realtime API 的這裡少一層 "function"
    # 這是和 ChatCompletion 不一樣的地方
    "name": "google_res",                # 函式名稱
    "description": "取得 Google 搜尋結果", # 函式說明
    "parameters": GoogleRes.model_json_schema(), # 參數規格
}]

async def main():
    client = AsyncOpenAI()

    async with client.beta.realtime.connect(model="gpt-4o-realtime-preview") as connection:
        await connection.session.update(
            session={
                'modalities': ['text'],
                'tools': tools,
                "tool_choice": "auto"
            }
        )

        await connection.conversation.item.create(
            item={
                "type": "message",
                "role": "user",
                "content": [{
                    "type": "input_text", 
                    "text": "十二強棒球賽冠軍是哪一隊？"
                }],
            }
        )
        await connection.response.create(
            # response={
            #     'tools': tools,
            #     "tool_choice": "auto"
            # }
        )

        async for event in connection:
            print(event.type)
            if event.type == 'response.text.delta':
                # print(event.delta, flush=True, end="")
                pass

            elif event.type == 'response.text.done':
                print(event.text)
            elif event.type == "response.done":
                # 如果伺服端回應需要叫用函式
                if event.response.output[0].type == "function_call":
                    func = event.response.output[0].name
                    args = event.response.output[0].arguments
                    # pprint(event.response)
                    print(f'\tcall {func}(**{args})')
                    # 將函式叫用結果傳回伺服端
                    await connection.conversation.item.create(
                        item={
                            "type": "function_call_output",
                            "call_id": event.response.output[0].call_id,
                            "output": eval(f'{func}(**{args})')
                        }
                    )
                    # 請伺服端重新生成回應
                    await connection.response.create()
                else:
                    break
            elif event.type == "error":
                print(f'\t{event.error.message}')

asyncio.run(main())