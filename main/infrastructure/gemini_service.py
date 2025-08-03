"""
Geminiサービスの実装（リファクタリング版）
ILLMServiceインターフェースの具体的な実装
"""

import subprocess
import json
from main.application.interfaces import ILLMService
from main.infrastructure.prompt_injector_service import PromptInjectorService
from main.domain.models import Message


class GeminiService(ILLMService):
    """Gemini APIを使ったLLMサービス（プロンプトインジェクター統合版）"""

    def __init__(self, prompt_injector: PromptInjectorService,
                 timeout: int = 90):
        """
        Args:
            prompt_injector: プロンプト構築サービス
            timeout: API呼び出しのタイムアウト時間（秒）
        """
        self.prompt_injector = prompt_injector
        self.timeout = timeout

    def generate_response(self, agent_id: str, context: Message) -> Message:
        """エージェントIDとコンテキストメッセージから応答を生成する"""
        # 1. プロンプトインジェクターにプロンプトの構築を依頼
        prompt = self.prompt_injector.build_prompt(agent_id, context)

        # 2. Gemini CLIを呼び出す（ハードコーディングされたロジックは削除）
        response_text = self._call_gemini_cli(prompt)

        # 3. 応答テキストをパースしてMessageオブジェクトを返す
        return self._parse_response(response_text, agent_id, context)

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

    def _parse_response(self, response_text: str, sender_id: str,
                        original_context: Message) -> Message:
        """応答テキストをパースしてMessageオブジェクトを作成"""
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
