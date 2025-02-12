# OpenAI Realtime API 測試範例

這是 OpenAI Realtime API 的測試範例，可參考對應的[教學文件](https://hackmd.io/@meebox/SkXzrxvFyg)：

- realtime_api_text.py

    OpenAI Python 套件中 realtime API 文件上的[簡易範例](https://github.com/openai/openai-python/tree/7193688e364bd726594fe369032e813ced1bdfe2?tab=readme-ov-file#realtime-api-beta)，示範如何透過文字使用該 API。

- realtime_api_VAD.py

    以 OpenAI 自己的 [push_to_talk_app.py 範例]((https://github.com/openai/openai-python/tree/7193688e364bd726594fe369032e813ced1bdfe2/examples/realtime))為雛形，拿掉原本用 Textual 包裝的使用者介面，讓程式更簡單，以便專注在 Realtime API。

- audio_util.py

    這是伴隨 push_to_talk_app.py 範例的[工具模組](https://github.com/openai/openai-python/blob/7193688e364bd726594fe369032e813ced1bdfe2/examples/realtime/audio_util.py)，用來播放聲音。

- realtime_api_VAD_off.py

    這是 realtime_api_VAD.py 關閉 [VAD 功能](https://platform.openai.com/docs/guides/realtime-model-capabilities#voice-activity-detection-vad)的測試版本，以便瞭解自行提交串流語音的方式。

- realtime_api_text_tool.py

    這是為 realtime_api_text.py 加上 [function calling 功能](https://platform.openai.com/docs/guides/realtime-model-capabilities#function-calling)的版本，以便瞭解如何使用 function calling，同時也加上了簡單的錯誤處理機制。