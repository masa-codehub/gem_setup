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
    def __init__(self, agent_id: str, mode: str = 'clean'):
        self.agent_id = agent_id
        self.mode = mode

        # 依存性の注入（新アーキテクチャ対応）
        self.message_broker = SqliteMessageBroker()
        try:
            with self.message_broker:
                self.message_broker.initialize_db()
        except Exception:
            print("Message broker initialization failed")

        # プロンプトリポジトリとインジェクターの初期化（依存性注入）
        try:
            self.prompt_repository = FileBasedPromptRepository()
            self.prompt_injector = PromptInjectorService(
                self.prompt_repository)
        except Exception as e:
            print(f"Prompt services initialization failed: {e}")
            self.prompt_repository = None
            self.prompt_injector = None

        # LLMサービスの初期化（依存性注入）
        try:
            self.llm_service = GeminiService(self.prompt_injector)
        except Exception as e:
            print(f"LLM service initialization failed: {e}")
            self.llm_service = None

        try:
            self.react_service = ReActService(
                self.llm_service,
                self.message_broker
            )
        except Exception:
            print("ReAct service initialization failed")
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
            # エージェントのペルソナを読み込む
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
            agent_name = agent_file_map.get(self.agent_id,
                                            self.agent_id.lower())
            config_file = f"/app/config/{agent_name}.md"
            with open(config_file, 'r') as f:
                persona = f.read()

            # ReActServiceを使用してメッセージを処理
            response = self.react_service.think_and_act(
                self.agent_id, persona, [message])
            if response:
                self.message_broker.post_message(response)
            return None
        except Exception as e:
            print(f"[{self.agent_id}] Error in clean mode: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _handle_message_legacy(self, message: Message) -> Optional[str]:
        """レガシーモードでメッセージを処理"""
        # レガシー処理の実装（今後の拡張用）
        msg_type = message.message_type
        print(f"[{self.agent_id}] Legacy mode processing: {msg_type}")
        return None
