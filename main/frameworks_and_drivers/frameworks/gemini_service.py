"""
Geminiサービスの実装（リファクタリング版）
ILLMServiceインターフェースの具体的な実装
"""

import subprocess
import json
import logging
from typing import Optional, Dict, Any

from main.use_cases.interfaces.interfaces import ILLMService
from main.frameworks_and_drivers.frameworks.prompt_injector_service import (
    PromptInjectorService
)
from main.entities.models import Message


class GeminiService(ILLMService):
    """Gemini APIを使ったLLMサービス（プロンプトインジェクター統合版）"""

    def __init__(self,
                 prompt_injector: PromptInjectorService = None,
                 timeout: int = 90,
                 mcp_server_name: Optional[str] = None):
        """
        Args:
            prompt_injector: プロンプト構築サービス
            timeout: API呼び出しのタイムアウト時間（秒）
            mcp_server_name: 接続するMCPサーバー名
        """
        self.prompt_injector = prompt_injector
        self.timeout = timeout
        self.mcp_server_name = mcp_server_name
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - GeminiService - %(levelname)s - %(message)s'
        )

    def generate_response(self, agent_id: str, context: Message) -> Message:
        """エージェントIDとコンテキストメッセージから応答を生成する（レガシーメソッド）"""
        # 1. プロンプトインジェクターにプロンプトの構築を依頼
        prompt = self.prompt_injector.build_prompt(agent_id, context)

        # 2. Gemini CLIを呼び出す（ハードコーディングされたロジックは削除）
        response_text = self._call_gemini_cli(prompt)

        # 3. 応答テキストをパースしてMessageオブジェクトを返す
        # レガシー互換性のために、必ずMessageオブジェクトを返す
        result = self._parse_response(response_text, agent_id, context)
        if result is None:
            # フォールバック: エラー時でもMessageオブジェクトを返す
            return Message(
                recipient_id=context.sender_id,
                sender_id=agent_id,
                message_type="RESPONSE",
                payload={"content": response_text, "error": True},
                turn_id=context.turn_id + 1
            )
        return result

    def generate_structured_response(
        self,
        agent_id: str,
        context: Message,
        generation_config: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None
    ) -> Optional[Message]:
        """
        コンテキストに基づき、構造化されたMessageオブジェクトを生成する。

        Args:
            agent_id: 応答を生成するエージェントのID
            context: 応答の基となるコンテキストメッセージ
            generation_config: temperatureなどの生成設定
            model: 使用するモデル (例: 'gemini-1.5-flash')

        Returns:
            LLMが生成したMessageオブジェクト。パース失敗時はNone。
        """
        # 1. プロンプトインジェクターにプロンプトの構築を依頼
        prompt = self.prompt_injector.build_prompt(agent_id, context)

        # 2. Gemini CLIのコマンドを動的に構築
        command = self._build_command(prompt, model)

        try:
            # 3. サブプロセスとしてGemini CLIを実行
            logging.info(f"Executing command: {' '.join(command)}")
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,  # エラー時に例外を発生させる
                encoding='utf-8'  # 文字化け防止
            )

            # 4. 応答テキストをパースしてMessageオブジェクトを返す
            return self._parse_response(process.stdout)

        except subprocess.CalledProcessError as e:
            logging.error("Gemini CLI execution failed.")
            logging.error("Return Code: %s", e.returncode)
            logging.error("Stdout: %s", e.stdout)
            logging.error("Stderr: %s", e.stderr)
            return None
        except Exception as e:
            logging.error(
                "An unexpected error occurred in GeminiService: %s", e
            )
            return None

    def _build_command(self, prompt: str, model: Optional[str]) -> list[str]:
        """
        レポートで詳述されている設定オプションを基に、
        gemini-cliのコマンドリストを構築する。
        """
        command = ["gemini"]

        # --allowed-mcp-server-names: MCPサーバー名を指定
        if self.mcp_server_name:
            command.extend([
                "--allowed-mcp-server-names",
                self.mcp_server_name
            ])

        # -m, --model: 使用するモデルを指定 (コマンドライン引数)
        if model:
            command.extend(["-m", model])

        # -p, --prompt: プロンプトを指定
        command.extend(["-p", prompt])

        return command

    def _call_gemini_cli(self, prompt: str) -> str:
        """Gemini CLIを呼び出して応答を取得"""
        try:
            # gemini-cliコマンドを実行
            result = subprocess.run(
                ['gemini-cli', '--prompt', prompt],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr}"

        except subprocess.TimeoutExpired:
            return "Error: Gemini API call timed out"
        except Exception as e:
            return f"Error: {str(e)}"

    def _parse_response(self, response_text: str, sender_id: str = None,
                        original_context: Message = None) -> Optional[Message]:
        """
        応答テキストをパースしてMessageオブジェクトを作成

        Args:
            response_text: パースする応答テキスト
            sender_id: 送信者ID（レガシー互換性用）
            original_context: 元のコンテキスト（レガシー互換性用）
        """
        try:
            # Gemini CLIの応答から最初のJSONオブジェクトを抽出する
            json_start = response_text.find('{')
            json_end = response_text.rfind('}')
            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end+1]
                response_dict = json.loads(json_str)

                # payloadが文字列化されている場合があるため、再度パースを試みる
                if isinstance(response_dict.get("payload"), str):
                    try:
                        response_dict["payload"] = json.loads(
                            response_dict["payload"]
                        )
                    except json.JSONDecodeError:
                        logging.warning(
                            "Payload was a string but not valid JSON. "
                            "Keeping as is."
                        )

                return Message(**response_dict)
            else:
                logging.error(
                    "No JSON object found in response: %s", response_text
                )
                return None

        except (json.JSONDecodeError, TypeError) as e:
            logging.error(f"Failed to parse JSON from response: {e}")
            logging.error(f"Raw response text: {response_text}")

            # レガシー互換性: フォールバック処理
            if sender_id and original_context:
                return self._legacy_parse_fallback(
                    response_text, sender_id, original_context
                )
            return None

    def _legacy_parse_fallback(self, response_text: str, sender_id: str,
                               original_context: Message) -> Message:
        """レガシー互換性のためのフォールバック処理"""
        try:
            # JSONレスポンスを期待
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                json_text = response_text[json_start:json_end].strip()
                data = json.loads(json_text)

                return Message(
                    recipient_id=data.get('recipient_id', 'SYSTEM'),
                    sender_id=sender_id,
                    message_type=data.get('message_type', 'RESPONSE'),
                    payload=data.get('payload', {}),
                    turn_id=original_context.turn_id + 1
                )

        except (json.JSONDecodeError, KeyError):
            pass

        # JSONパースに失敗した場合のフォールバック
        return Message(
            recipient_id=original_context.sender_id,
            sender_id=sender_id,
            message_type="RESPONSE",
            payload={"content": response_text},
            turn_id=original_context.turn_id + 1
        )
