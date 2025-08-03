"""
TDD Phase 3: ペルソナ（プロンプト）の修正機能テスト

新しいメッセージタイプに対応したプロンプトの動作を確認
Kent BeckのTDD思想: 実装を進める前にテストで期待する動作を定義
"""

import pytest
import os
from unittest.mock import patch, mock_open


class TestPersonaPromptModificationsTDD:
    """ペルソナ（プロンプト）ファイルの修正機能のTDDテスト"""

    def test_moderator_persona_file_exists(self):
        """RED: moderator.mdファイルが存在することを確認"""
        moderator_path = "config/moderator.md"
        assert os.path.exists(moderator_path), "moderator.md should exist"

    def test_debater_a_persona_file_exists(self):
        """RED: debater_a.mdファイルが存在することを確認"""
        debater_a_path = "config/debater_a.md"
        assert os.path.exists(debater_a_path), "debater_a.md should exist"

    def test_moderator_persona_contains_initiate_debate_handling(self):
        """RED: moderator.mdにINITIATE_DEBATEの処理が記載されていることをテスト"""
        moderator_path = "config/moderator.md"

        with open(moderator_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 新しいメッセージタイプへの対応が記載されているかチェック
        assert "INITIATE_DEBATE" in content, \
            "moderator.md should contain INITIATE_DEBATE handling"
        assert "DEBATE_BRIEFING" in content, \
            "moderator.md should reference DEBATE_BRIEFING response"
        assert "REQUEST_STRATEGY" in content, \
            "moderator.md should reference REQUEST_STRATEGY response"

    def test_debater_a_persona_contains_strategy_handling(self):
        """RED: debater_a.mdにSUBMIT_STRATEGYの処理が記載されていることをテスト"""
        debater_a_path = "config/debater_a.md"

        with open(debater_a_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 戦略提出への対応が記載されているかチェック
        assert "REQUEST_STRATEGY" in content, \
            "debater_a.md should handle REQUEST_STRATEGY messages"
        assert "SUBMIT_STRATEGY" in content, \
            "debater_a.md should respond with SUBMIT_STRATEGY"

    def test_moderator_persona_state_transition_logic(self):
        """RED: moderator.mdに状態遷移ロジックが記載されていることをテスト"""
        moderator_path = "config/moderator.md"

        with open(moderator_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 状態遷移ロジックが記載されているかチェック
        assert "STATE TRANSITIONS" in content, \
            "moderator.md should contain state transition logic"

        # 具体的な遷移ルールが記載されているかチェック
        assert "If `INITIATE_DEBATE`:" in content, \
            "moderator.md should define INITIATE_DEBATE transition"

    def test_debater_a_persona_response_types(self):
        """RED: debater_a.mdに応答タイプが明確に定義されていることをテスト"""
        debater_a_path = "config/debater_a.md"

        with open(debater_a_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 応答タイプが明確に定義されているかチェック
        assert "YOUR RESPONSE TYPES:" in content, \
            "debater_a.md should define response types"
        assert "SUBMIT_STRATEGY" in content, \
            "debater_a.md should define SUBMIT_STRATEGY response"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
