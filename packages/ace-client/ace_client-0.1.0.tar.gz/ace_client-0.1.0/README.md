# ace-py

## 概要

`ace-py` は来栖川電算の CLI 型 AI エージェント [ACE](https://github.com/kurusugawa-computer/ace) を
Python から簡単に利用するためのラッパーライブラリです。

## インストール

```bash
pip install ace-client
```

または uv を使用する場合:

```bash
uv add ace-client
```

## 使用例

簡単な使用例です。環境変数 `OPENAI_API_KEY` に API キーを入れて実行します。

```python
import asyncio
import os

import msgspec

from ace_client import Ace


class Response(msgspec.Struct):
    answer: str


async def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("環境変数 OPENAI_API_KEY を設定してください", file=sys.stderr)
        sys.exit(1)

    ace = Ace(api_key=api_key)

    try:
        # 30秒のタイムアウトを設定してACEを呼び出す
        # イベントをトリガーにしてキャンセルしたい場合はTaskGroup等を使用して明示的にキャンセルを呼び出してください
        async with asyncio.timeout(30):
            result = await ace.invoke(
                config_path="example/simple.yaml",
                agent_name="root",
                input_data={"question": "今日の名古屋の天気は？"},
            )
            response = result.unmarshal(Response)
            print(response.answer)

    except Exception as e:
        print(f"エラーが発生しました: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
```

## ライセンス

MIT License
