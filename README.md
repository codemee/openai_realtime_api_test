# OpenAI Realtime API 測試範例

這是 OpenAI Realtime API 的測試範例：

## push_to_talk_app.py

OpenAI 自己的[範例](https://github.com/openai/openai-python/tree/7193688e364bd726594fe369032e813ced1bdfe2/examples/realtime)，使用 Textual 製作使用者介面。

## audio_util.py

這是伴隨 push_to_talk_app.py 的工具模組，用來播放聲音。

## real_api_console.py

以 push_to_talk_app.py 為雛形，拿掉原本用 Textual 包裝的使用者介面，讓程式更簡單，以便專注在 Realtime API。

## simple_text.py

OpenAI realtime API 文件上的簡易範例，示範如何透過文字使用該 API。