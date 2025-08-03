"""
Kent BeckのTDD思想に基づく GeminiService リファクタリング

TDDサイクル: Red → Green → Refactor
1. まず失敗するテストを書く (Red)
2. 最小限の実装でテストを通す (Green)
3. コードを整理する (Refactor)
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import subprocess

from main.entities.models import Message
from main.frameworks_and_drivers.frameworks.prompt_injector_service import PromptInjectorService


class TestGeminiServiceRefactoredTDD(unittest.TestCase):
    """TDD思想に基づくGeminiServiceリファクタリングテスト"""

    def setUp(self):
        """各テスト前の共通セットアップ"""
        self.mock_prompt_injector = Mock(spec=PromptInjectorService)
        self.mock_prompt_injector.build_prompt.return_value = "test prompt"

    def test_generate_structured_response_with_model_parameter(self):
        """
        Red Phase: 新しいmodel引数を受け取るgenerate_structured_responseメソッドのテスト
        まだ実装されていないので失敗する
        """
        from main.frameworks_and_drivers.frameworks.gemini_service import GeminiService

        service = GeminiService(
            prompt_injector=self.mock_prompt_injector,
            mcp_server_name="test-server"
        )

        context = Message(
            recipient_id="MODERATOR",
            sender_id="SYSTEM",
            message_type="START_SESSION",
            payload={"topic": "AI Ethics"},
            turn_id=0
        )

        # この時点では generate_structured_response メソッドは存在しない
        # テストは失敗するはず (Red)
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ('{"recipient_id": "DEBATER_A", '
                                  '"sender_id": "MODERATOR", '
                                  '"message_type": "RESPONSE", '
                                  '"payload": {"content": "test"}, '
                                  '"turn_id": 1}')
            mock_run.return_value = mock_result

            # model引数を指定して呼び出し
            response = service.generate_structured_response(
                agent_id="MODERATOR",
                context=context,
                model="gemini-1.5-flash"
            )

            # 期待する結果の検証
            self.assertIsInstance(response, Message)
            self.assertEqual(response.recipient_id, "DEBATER_A")

    def test_build_command_with_mcp_server_and_model(self):
        """
        Red Phase: MCPサーバーとモデルを指定したコマンド構築のテスト
        まだ実装されていないので失敗する
        """
        from main.frameworks_and_drivers.frameworks.gemini_service import GeminiService

        service = GeminiService(
            prompt_injector=self.mock_prompt_injector,
            mcp_server_name="test-server"
        )

        # _build_commandメソッドはまだ存在しない
        # テストは失敗するはず (Red)
        command = service._build_command("test prompt", "gemini-1.5-flash")

        expected_command = [
            "gemini",
            "--allowed-mcp-server-names", "test-server",
            "-m", "gemini-1.5-flash",
            "-p", "test prompt"
        ]

        self.assertEqual(command, expected_command)

    def test_parse_response_with_json_extraction(self):
        """
        Red Phase: JSON応答を賢く抽出するパーサーのテスト
        まだ実装されていないので失敗する
        """
        from main.frameworks_and_drivers.frameworks.gemini_service import GeminiService

        service = GeminiService(
            prompt_injector=self.mock_prompt_injector
        )

        # Gemini CLIの応答に思考プロセスなどが含まれるケース
        response_text = """
        思考: ユーザーの質問を分析します...
        
        {"recipient_id": "DEBATER_A", "sender_id": "MODERATOR", "message_type": "RESPONSE", "payload": {"content": "analyzed response"}, "turn_id": 1}
        
        追加情報: この応答は...
        """

        # _parse_responseメソッドの新しい実装はまだ存在しない
        # テストは失敗するはず (Red)
        message = service._parse_response(response_text)

        self.assertIsInstance(message, Message)
        self.assertEqual(message.recipient_id, "DEBATER_A")
        self.assertEqual(message.payload["content"], "analyzed response")

    def test_error_handling_with_subprocess_exception(self):
        """
        Red Phase: subprocess.CalledProcessErrorの詳細ハンドリング
        まだ実装されていないので失敗する
        """
        from main.frameworks_and_drivers.frameworks.gemini_service import GeminiService

        service = GeminiService(
            prompt_injector=self.mock_prompt_injector
        )

        context = Message(
            recipient_id="MODERATOR",
            sender_id="SYSTEM",
            message_type="START_SESSION",
            payload={"topic": "test"},
            turn_id=0
        )

        with patch('subprocess.run') as mock_run:
            # subprocess.CalledProcessErrorを発生させる
            error = subprocess.CalledProcessError(
                returncode=1,
                cmd=['gemini'],
                output="stdout output",
                stderr="stderr output"
            )
            mock_run.side_effect = error

            # 新しいエラーハンドリングはまだ実装されていない
            # テストは失敗するはず (Red)
            response = service.generate_structured_response(
                agent_id="MODERATOR",
                context=context
            )

            # エラー時はNoneを返すことを期待
            self.assertIsNone(response)

    def test_generation_config_parameter_support(self):
        """
        Red Phase: generation_configパラメータのサポート（将来拡張用）
        まだ実装されていないので失敗する
        """
        from main.frameworks_and_drivers.frameworks.gemini_service import GeminiService

        service = GeminiService(
            prompt_injector=self.mock_prompt_injector
        )

        context = Message(
            recipient_id="MODERATOR",
            sender_id="SYSTEM",
            message_type="START_SESSION",
            payload={"topic": "test"},
            turn_id=0
        )

        generation_config = {
            "temperature": 0.8,
            "max_tokens": 1000
        }

        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ('{"recipient_id": "DEBATER_A", '
                                  '"sender_id": "MODERATOR", '
                                  '"message_type": "RESPONSE", '
                                  '"payload": {}, '
                                  '"turn_id": 1}')
            mock_run.return_value = mock_result

            # generation_configパラメータはまだサポートされていない
            # テストは失敗するはず (Red)
            response = service.generate_structured_response(
                agent_id="MODERATOR",
                context=context,
                generation_config=generation_config
            )

            self.assertIsInstance(response, Message)


if __name__ == '__main__':
    unittest.main()
