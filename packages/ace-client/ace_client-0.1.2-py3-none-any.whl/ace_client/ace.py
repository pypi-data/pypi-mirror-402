"""Aceクライアントの定義."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TextIO

from ace_client.invoke import InvokeOptions, Result, invoke


class Ace:
    """aceコマンドをラップするクライアントクラス.

    内部で実行コマンドのパスや認証用のAPIキーを保持します。

    Attributes:
        executable_path: aceコマンドの実行パス（デフォルト: "ace"）
        api_key: OpenAIのAPIキー

    """

    def __init__(
        self,
        *,
        executable_path: str = "ace",
        api_key: str | None = None,
    ) -> None:
        """ACEのインスタンスを作成します.

        Args:
            executable_path: aceコマンドの実行パス（デフォルト: "ace"）
            api_key: OpenAIのAPIキー

        """
        self.executable_path = executable_path
        self.api_key = api_key

    async def invoke(
        self,
        config_path: str,
        agent_name: str,
        input_data: Mapping[str, Any],
        *,
        workdir: str | None = None,
        log_writer: TextIO | None = None,
        log_level: str | None = None,
    ) -> Result:
        """ACEを実行して結果を返します.

        Args:
            config_path: 設定ファイルのパス
            agent_name: エージェント名
            input_data: 入力データ
            workdir: 実行時のカレントディレクトリ
            log_writer: ログの出力先
            log_level: ログレベル（error, warn, info, debug, trace, off）

        Returns:
            ACEの実行結果

        Raises:
            RuntimeError: 実行に失敗した場合

        """
        options = InvokeOptions(
            workdir=workdir,
            log_writer=log_writer,
            log_level=log_level,
        )
        return await invoke(
            executable_path=self.executable_path,
            api_key=self.api_key,
            config_path=config_path,
            agent_name=agent_name,
            input_data=input_data,
            options=options,
        )
