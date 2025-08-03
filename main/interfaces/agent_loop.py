"""
Agent Loop - TDD Green Phase
エージェントのメインループ実装
"""
import time
from typing import Optional
from main.infrastructure.message_broker import SqliteMessageBroker
from main.infrastructure.gemini_service import GeminiService
from main.infrastructure.prompt_injector_service import PromptInjectorService
from main.domain.models import Message


class AgentLoop:
    """エージェントのメインループ - 自律的な思考→行動サイクル"""

    def __init__(self, agent_id: str):
        """
        エージェントループを初期化

        Args:
            agent_id: エージェントID
        """
        self.agent_id = agent_id

        # 依存性注入: 必要なサービスを初期化
        self.message_bus = SqliteMessageBroker()
        self.message_bus.initialize_db()

        self.prompt_injector = PromptInjectorService()
        self.llm = GeminiService()

    def run(self) -> None:
        """エージェントのメインループを開始"""
        print(f"[{self.agent_id}] Starting agent loop...")

        while True:
            try:
                # 1. A2Aメッセージバスから自分宛のメッセージを確認
                message = self.message_bus.get_message(self.agent_id)
                if message:
                    print(
                        f"[{self.agent_id}] Processing message: {message.message_type}")
                    self._process_message(message)
                else:
                    print(f"[{self.agent_id}] No messages, waiting...")

                time.sleep(5)

            except Exception as e:
                print(f"[{self.agent_id}] Error in agent loop: {e}")
                time.sleep(5)

    def _process_message(self, message: Message) -> None:
        """メッセージを処理する"""
        try:
            # プロンプトを構築
            context = {
                'message': message,
                'current_turn': message.turn_id
            }
            prompt = self.prompt_injector.build_prompt(self.agent_id, context)

            # LLMで応答を生成
            response_text = self.llm.generate_response(prompt)

            # レスポンスからメッセージを生成
            response_message = self._parse_response_to_message(
                message, response_text
            )

            if response_message:
                self.message_bus.post_message(response_message)
                print(
                    f"[{self.agent_id}] Sent response to {response_message.recipient_id}")

        except Exception as e:
            print(f"[{self.agent_id}] Error processing message: {e}")

    def _parse_response_to_message(self, original_message: Message, response_text: str) -> Optional[Message]:
        """LLMのレスポンスをメッセージに変換（簡易実装）"""
        # 簡易実装：MODERATORに応答を送信
        return Message(
            sender_id=self.agent_id,
            recipient_id="MODERATOR",
            message_type="SUBMIT_STATEMENT",
            payload={"content": response_text},
            turn_id=original_message.turn_id + 1
        )
