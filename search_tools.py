from googlesearch import search
from pydantic import BaseModel, Field

def google_res(keyword, num_results=5, verbose=False):
    content = "以下為已發生的事實：\n"               # 強調資料可信度
    for res in search(keyword, advanced=True,    # 一一串接搜尋結果
                      num_results=num_results,
                      lang='zh-TW'):
        content += f"標題：{res.title}\n" \
                   f"摘要：{res.description}\n\n"
    if verbose:
        print('------------')
        print(content)
        print('------------')
    return content

# 描述 google_res 工具函式的參數
class GoogleRes(BaseModel):
    keyword: str = Field(description='要搜尋的關鍵字')
