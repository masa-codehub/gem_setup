"""
TDD Red Phase: 高度なディベート開始機能のテスト
run_debate.shと同等の機能をplatform_supervisor.pyで実現するためのテスト
"""
import pytest
import tempfile
import os
import yaml
from unittest.mock import MagicMock, patch
from main.platform.supervisor import Supervisor


class TestSupervisorAdvancedDebateFeatures:
    """高度なディベート開始機能のテスト（TDD Red Phase）"""

    def setup_method(self):
        """各テストメソッド前のセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_file = os.path.join(self.temp_dir, "advanced_project.yml")

        # より詳細なプロジェクト定義
        project_def = {
            'project_name': 'advanced_debate_platform',
            'description': 'Advanced AI debate system',
            'agents': [
                {
                    'id': 'MODERATOR',
                    'type': 'moderator',
                    'description': 'Debate moderator'
                },
                {
                    'id': 'DEBATER_A',
                    'type': 'debater',
                    'description': 'Affirmative debater'
                },
                {
                    'id': 'DEBATER_N',
                    'type': 'debater',
                    'description': 'Negative debater'
                },
                {
                    'id': 'JUDGE_L',
                    'type': 'judge',
                    'description': 'Logic judge'
                },
            ],
            'message_bus': {
                'type': 'sqlite',
                'db_path': 'advanced_messages.db'
            },
            'initial_task': {
                'type': 'debate',
                'topic': 'Advanced AI ethics discussion',
                'metadata': {
                    'difficulty': 'expert',
                    'duration': 600,
                    'format': 'structured'
                }
            },
            'platform': {
                'timeout': 600,
                'agent_check_interval': 5,
                'auto_restart': True
            }
        }

        with open(self.project_file, 'w') as f:
            yaml.dump(project_def, f)

    def teardown_method(self):
        """各テストメソッド後のクリーンアップ"""
        if os.path.exists(self.project_file):
            os.remove(self.project_file)

    def test_post_initial_message_with_metadata_enhancement(self):
        """
        🔴 FAILING TEST: 初期メッセージにメタデータも含めて送信する機能
        run_debate.shのような詳細な情報を含む初期化
        """
        supervisor = Supervisor(self.project_file)

        # メッセージバスをモック化
        mock_message_bus = MagicMock()
        supervisor.message_bus = mock_message_bus

        # 拡張された初期メッセージ投函
        topic = "Enhanced debate topic"
        supervisor.post_initial_message_with_metadata(topic)

        # 検証: メッセージにメタデータが含まれている
        sent_message = mock_message_bus.post_message.call_args[0][0]
        assert 'metadata' in sent_message.payload
        assert 'session_id' in sent_message.payload
        assert 'timestamp' in sent_message.payload
        metadata = sent_message.payload['metadata']
        assert metadata['platform_version'] == 'TDD-v1.0'

    def test_validate_agents_before_initial_message(self):
        """
        🔴 FAILING TEST: 初期メッセージ送信前にエージェントの準備完了を確認
        """
        supervisor = Supervisor(self.project_file)

        # メッセージバスをモック化
        mock_message_bus = MagicMock()
        supervisor.message_bus = mock_message_bus

        # エージェントの準備状況を検証する機能
        with patch.object(supervisor, 'are_agents_ready', return_value=False):
            with pytest.raises(RuntimeError, match="Agents not ready"):
                supervisor.post_initial_message_with_validation("Test topic")

    def test_post_multiple_initial_messages_for_different_agent_types(self):
        """
        🔴 FAILING TEST: 異なるタイプのエージェントに適切な初期メッセージを送信
        """
        supervisor = Supervisor(self.project_file)

        # メッセージバスをモック化
        mock_message_bus = MagicMock()
        supervisor.message_bus = mock_message_bus

        # 複数エージェントタイプに応じた初期化
        supervisor.post_initial_messages_by_agent_type("Debate topic")

        # 検証: 複数のメッセージが送信される
        assert mock_message_bus.post_message.call_count >= 2

        # MODERATORには司会開始メッセージ
        call_args_list = mock_message_bus.post_message.call_args_list
        moderator_calls = [
            call for call in call_args_list
            if call[0][0].recipient_id == 'MODERATOR'
        ]
        assert len(moderator_calls) >= 1

        # JUDGEには審査準備メッセージ
        judge_calls = [
            call for call in call_args_list
            if 'JUDGE' in call[0][0].recipient_id
        ]
        assert len(judge_calls) >= 1

    def test_post_initial_message_with_session_management(self):
        """
        🔴 FAILING TEST: セッション管理機能付きの初期メッセージ投函
        """
        supervisor = Supervisor(self.project_file)

        # メッセージバスをモック化
        mock_message_bus = MagicMock()
        supervisor.message_bus = mock_message_bus

        # セッション管理付きの初期化
        session_config = {
            'session_name': 'Expert Debate Session',
            'max_turns': 20,
            'time_limit': 600
        }

        session_topic = "Test topic"
        supervisor.post_initial_message_with_session(
            session_topic, session_config)

        # 検証
        sent_message = mock_message_bus.post_message.call_args[0][0]
        assert 'session_config' in sent_message.payload
        session_cfg = sent_message.payload['session_config']
        assert session_cfg['session_name'] == 'Expert Debate Session'

    def test_post_initial_message_handles_agent_startup_delay(self):
        """
        🔴 FAILING TEST: エージェント起動遅延を考慮した初期メッセージ送信
        """
        supervisor = Supervisor(self.project_file)

        # メッセージバスをモック化
        mock_message_bus = MagicMock()
        supervisor.message_bus = mock_message_bus

        # 起動遅延を考慮した初期化（リトライ機能付き）
        with patch('time.sleep'):  # テスト高速化のためsleepをモック
            topic = "Test topic"
            supervisor.post_initial_message_with_retry(topic, max_retries=3)

        # 検証: メッセージが送信される
        mock_message_bus.post_message.assert_called()

    def test_generate_session_statistics_after_initial_message(self):
        """
        🔴 FAILING TEST: 初期メッセージ送信後の統計情報生成
        """
        supervisor = Supervisor(self.project_file)

        # メッセージバスをモック化
        mock_message_bus = MagicMock()
        supervisor.message_bus = mock_message_bus

        # 統計機能付きの初期化
        supervisor.post_initial_message_with_stats("Test topic")

        # 統計情報の確認
        stats = supervisor.get_initialization_stats()
        assert 'initial_messages_sent' in stats
        assert 'session_start_time' in stats
        assert stats['initial_messages_sent'] >= 1

    def test_post_initial_message_with_config_validation(self):
        """
        🔴 FAILING TEST: プロジェクト設定の妥当性検証付き初期化
        """
        supervisor = Supervisor(self.project_file)

        # メッセージバスをモック化
        mock_message_bus = MagicMock()
        supervisor.message_bus = mock_message_bus

        # 設定検証付きの初期化
        topic = "Test topic"
        supervisor.post_initial_message_with_config_validation(topic)

        # 検証: 設定が適切に確認される
        assert supervisor.config_validated is True

        # 不正な設定での失敗テスト
        supervisor.project_def['agents'] = []  # エージェントなし
        with pytest.raises(ValueError, match="No agents defined"):
            topic2 = "Test topic"
            supervisor.post_initial_message_with_config_validation(topic2)
