"""Invoke関連の定義."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, TextIO

import msgspec
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent


class AceError(Exception):
    """ace-py固有の基底例外クラス."""

    pass


@dataclass
class InvokeOptions:
    """Invoke呼び出しに渡すオプション.

    Attributes:
        workdir: 実行時のカレントディレクトリ
        log_writer: ログの出力先（デフォルト: None）
        log_level: ログレベル（デフォルト: info、有効な値: error, warn, info, debug, trace, off）

    """

    workdir: str | None = None
    log_writer: TextIO | None = None
    log_level: str | None = field(default=None)


@dataclass
class Result:
    """ACEの実行結果.

    Attributes:
        text: 実行結果のテキスト

    """

    text: str

    def unmarshal[T](self, type_: type[T]) -> T:
        """結果をJSONとしてパースして指定した型に変換します.

        Args:
            type_: 変換先の型

        Returns:
            パースされたオブジェクト

        Raises:
            msgspec.ValidationError: バリデーションに失敗した場合
            msgspec.DecodeError: JSONのパースに失敗した場合

        """
        try:
            return msgspec.json.decode(self.text.encode("utf-8"), type=type_)
        except msgspec.DecodeError as e:
            raise AceError(f"JSON parse error: {e}\nResponse: {self.text}") from e
        except msgspec.ValidationError as e:
            raise AceError(f"Validation error: {e}") from e


async def invoke(
    *,
    executable_path: str,
    api_key: str | None,
    config_path: str,
    agent_name: str,
    input_data: Mapping[str, Any],
    options: InvokeOptions,
) -> Result:
    """ACEを実行して結果を返します.

    Args:
        executable_path: aceコマンドの実行パス
        api_key: OpenAIのAPIキー
        config_path: 設定ファイルのパス
        agent_name: エージェント名
        input_data: 入力データ
        options: 実行オプション

    Returns:
        ACEの実行結果

    Raises:
        AceError: 実行に失敗した場合

    """
    # ACEをMCPサーバーとして実行するコマンドを準備する
    args = ["mcp-server", "--config", config_path]

    if options.workdir is not None:
        args.extend(["--workdir", options.workdir])

    if options.log_level and options.log_level != "off":
        args.extend(["--log-level", options.log_level])

    args.append(agent_name)

    env = os.environ.copy()
    if api_key:
        env["OPENAI_API_KEY"] = api_key

    server_params = StdioServerParameters(
        command=executable_path,
        args=args,
        env=env,
    )

    # MCPクライアントを用意して、ACEのMCPサーバーを実行し、セッションをつくる
    try:
        async with stdio_client(server_params, errlog=options.log_writer) as (
            read_stream,
            write_stream,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                result = await session.call_tool(agent_name, dict(input_data))
                if not result.content or not isinstance(result.content[0], TextContent) or result.content[0].text == "":
                    raise AceError("Invalid response: content is empty or not TextContent")
                if result.isError:
                    raise AceError(f"Agent execution failed: {result.content[0].text}")

                return Result(text=result.content[0].text)

    except FileNotFoundError as e:
        raise AceError(f"Executable not found: {executable_path}") from e
    except asyncio.CancelledError as e:
        raise AceError("Execution was cancelled") from e
    except Exception as e:
        if isinstance(e, AceError):
            raise
        raise AceError(f"Unexpected error: {e}") from e
