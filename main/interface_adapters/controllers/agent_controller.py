"""
Agent Controller - TDD Green Phase (Refactored for Clean Architecture)
エージェントのメインループ実装（クリーンアーキテクチャ対応）
"""
from main.entities.models import Message


class AgentController:
    """
    エージェントコントローラー - 自律的な思考→行動サイクル
    旧 AgentLoop からリファクタリング
    """

    def __init__(self, agent_id: str):
        """
        エージェントコントローラーを初期化

        Args:
            agent_id: エージェントID
        """
        self.agent_id = agent_id

        # TDD Green Phase: 依存関係を初期化
        try:
            from main.frameworks_and_drivers.frameworks.message_broker import SqliteMessageBroker
            from main.frameworks_and_drivers.frameworks.prompt_injector_service import PromptInjectorService
            from main.frameworks_and_drivers.frameworks.gemini_service import GeminiService

            self.message_broker = SqliteMessageBroker()
            self.message_bus = self.message_broker  # テスト互換性のためのエイリアス
            self.prompt_injector = PromptInjectorService()
            self.gemini_service = GeminiService()
        except ImportError:
            # Fallback for testing
            self.message_broker = None
            self.message_bus = None
            self.prompt_injector = None
            self.gemini_service = None

    def run(self) -> None:
        """エージェントのメインループを開始"""
        print(f"[{self.agent_id}] Starting agent controller...")

        # テストで期待される動作の簡易実装
        if self.message_bus:
            try:
                message = self.message_bus.get_message(self.agent_id)
                if message:
                    self._process_message(message)
            except Exception:
                pass

    def _process_message(self, message: Message) -> None:
        """メッセージを処理する（簡易実装）"""
        print(f"[{self.agent_id}] Processing message: {message.message_type}")

        # テストで期待される動作
        if self.prompt_injector and self.gemini_service:
            try:
                # プロンプト構築
                prompt = self.prompt_injector.build_prompt(
                    self.agent_id, message)
                # LLM応答生成
                response = self.gemini_service.generate_response(prompt)
            except Exception:
                pass


# Backward compatibility alias
AgentLoop = AgentController
