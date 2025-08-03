"""
TDD Refactor Phase - Legacy Test Modernization
既存テストを新しいアーキテクチャに適応させる
"""
import unittest
from unittest.mock import Mock, patch
from main.infrastructure.gemini_service import GeminiService


class TestGeminiServiceModernized(unittest.TestCase):
    """GeminiServiceの現代化されたテスト"""

    @patch('subprocess.run')
    def test_generate_response_with_new_architecture(self, mock_run):
        """新アーキテクチャに適応したレスポンス生成テスト"""
        # 実際のGeminiServiceは既知のパターンマッチングを使用
        service = GeminiService()

        # MODERATORパターンでテスト
        prompt = "MODERATOR test with PROMPT_FOR_STATEMENT"
        response = service.generate_response(prompt)

        # Assert - 現在の実装に合わせた検証
        self.assertIn("```json", response)
        self.assertIn("DEBATER_A", response)
        self.assertIn("PROMPT_FOR_STATEMENT", response)

    @patch('subprocess.run')
    def test_generate_response_error_handling_modernized(self, mock_run):
        """現代化されたエラーハンドリングテスト"""
        # Arrange - エラー状況のモック
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "API Error occurred"
        mock_run.return_value = mock_result

        service = GeminiService()

        # Act
        response = service.generate_response("Test prompt")

        # Assert - エラー時は適切なJSONレスポンスが返る
        self.assertIn("SYSTEM_ERROR", response)
        self.assertIn("```json", response)


if __name__ == '__main__':
    unittest.main()
