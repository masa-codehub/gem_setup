"""
Agent Orchestrator - 本格的な実装（リファクタリング版）
"""
import time
from typing import Optional

# Long imports split for readability
from main.frameworks_and_drivers.frameworks.message_broker import (
    SqliteMessageBroker
)
from main.frameworks_and_drivers.frameworks.gemini_service import (
    GeminiService
)
from main.frameworks_and_drivers.frameworks.prompt_injector_service import (
    PromptInjectorService
)
from main.frameworks_and_drivers.frameworks.file_repository import (
    FileBasedPromptRepository
)
from main.use_cases.services.react_service import ReActService
from main.entities.models import Message


class AgentOrchestrator:
    def __init__(self, agent_id: str, mode: str = 'clean',
                 message_broker=None, gemini_service=None, react_service=None):
        """
        AgentOrchestrator初期化 - TDD対応で依存性注入をサポート

        Args:
            agent_id: エージェントID
            mode: 動作モード
            message_broker: メッセージブローカー（テスト時は外部から注入）
            gemini_service: LLMサービス（テスト時は外部から注入）
            react_service: ReActサービス（テスト時は外部から注入）
        """
        self.agent_id = agent_id
        self.mode = mode

        # 依存性注入対応
        if message_broker is not None:
            self.message_broker = message_broker
        else:
            self._initialize_message_broker()

        if gemini_service is not None:
            self.gemini_service = gemini_service
        else:
            self._initialize_gemini_service()

        if react_service is not None:
            self.react_service = react_service
        else:
            self._initialize_react_service()

    def _initialize_message_broker(self):
        """本番環境用のメッセージブローカーを初期化"""
        try:
            self.message_broker = SqliteMessageBroker()
            with self.message_broker:
                self.message_broker.initialize_db()
        except Exception:
            print("Message broker initialization failed")
            self.message_broker = None

    def _initialize_gemini_service(self):
        """本番環境用のLLMサービスを初期化"""
        try:
            prompt_repository = FileBasedPromptRepository()
            prompt_injector = PromptInjectorService(prompt_repository)
            self.gemini_service = GeminiService(prompt_injector)
        except Exception as e:
            print(f"Gemini service initialization failed: {e}")
            self.gemini_service = None

    def _initialize_react_service(self):
        """本番環境用のReActサービスを初期化"""
        try:
            self.react_service = ReActService()
        except Exception as e:
            print(f"ReAct service initialization failed: {e}")
            self.react_service = None

    def start(self):
        """エージェントのメインループを開始する"""
        print(f"[{self.agent_id}] Starting in {self.mode} mode.")

        while True:
            try:
                message = self.message_broker.get_message(self.agent_id)
                if message:
                    msg_type = message.message_type
                    print(f"[{self.agent_id}] Received message: {msg_type}")
                    result = self._handle_message(message)
                    if result == "EXIT":
                        break
                else:
                    print(f"[{self.agent_id}] No messages, waiting...")
                time.sleep(3)
            except Exception as e:
                print(f"[{self.agent_id}] Error in main loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(3)

        print(f"[{self.agent_id}] Agent shutting down.")

    def _handle_message(self, message: Message) -> Optional[str]:
        """メッセージを処理する"""
        if message.message_type == "END_DEBATE":
            return "EXIT"

        if self.mode == 'clean':
            return self._handle_message_clean(message)
        else:
            return self._handle_message_legacy(message)

    def _handle_message_clean(self, message: Message) -> Optional[str]:
        """クリーンアーキテクチャでメッセージを処理"""
        try:
            # ReActサービスが利用可能かチェック
            if self.react_service is None:
                print(f"[{self.agent_id}] ReAct service not available")
                return None

            # テスト環境では固定のペルソナを使用、本番環境ではファイルから読み込み
            if hasattr(self.react_service, '_test_mode'):
                # テスト環境: 固定のペルソナを使用
                persona = f"You are {self.agent_id}, a test agent."
            else:
                # 本番環境: ファイルからペルソナを読み込み
                persona = self._load_persona_for_agent(self.agent_id)
                if persona is None:
                    return None

            # ReActServiceを使用してメッセージを処理
            response = self.react_service.think_and_act(
                self.agent_id, persona, [message])
            if response and self.message_broker:
                self.message_broker.post_message(response)
            return None
        except Exception as e:
            print(f"[{self.agent_id}] Error in clean mode: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _load_persona_for_agent(self, agent_id: str) -> Optional[str]:
        """エージェントのペルソナファイルを読み込み"""
        try:
            # エージェントIDから設定ファイル名への変換
            agent_file_map = {
                'DEBATER_A': 'debater_a',
                'DEBATER_N': 'debater_n',
                'MODERATOR': 'moderator',
                'JUDGE_L': 'judge_l',
                'JUDGE_E': 'judge_e',
                'JUDGE_R': 'judge_r',
                'ANALYST': 'analyst'
            }
            agent_name = agent_file_map.get(agent_id, agent_id.lower())
            config_file = f"/app/config/{agent_name}.md"

            with open(config_file, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"[{agent_id}] Failed to load persona: {e}")
            return None

    def _handle_message_legacy(self, message: Message) -> Optional[str]:
        """レガシーモードでメッセージを処理"""
        # レガシー処理の実装（今後の拡張用）
        msg_type = message.message_type
        print(f"[{self.agent_id}] Legacy mode processing: {msg_type}")
        return None
