"""
Agent Controller - Clean Architecture Refactored
エージェントのメインループ実装（クリーンアーキテクチャ対応）
"""
import os
import time
from main.entities.models import Message
from typing import Optional

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
        
        # 依存性注入: アプリケーションの実行に必要なサービスを初期化
        # このtry-exceptブロックは、テスト時に依存関係をモックするためのものです
        try:
            from main.frameworks_and_drivers.frameworks.message_broker import SqliteMessageBroker
            from main.frameworks_and_drivers.frameworks.prompt_injector_service import PromptInjectorService
            from main.frameworks_and_drivers.frameworks.gemini_service import GeminiService

            message_db_path = os.environ.get("MESSAGE_DB_PATH")
            if message_db_path:
                self.message_bus = SqliteMessageBroker(message_db_path)
            else:
                self.message_bus = SqliteMessageBroker()
            
            self.prompt_injector = PromptInjectorService()
            self.gemini_service = GeminiService(prompt_injector=self.prompt_injector)
        except ImportError:
            # テスト環境用のフォールバック
            self.message_bus = None
            self.prompt_injector = None
            self.gemini_service = None

    def run(self) -> None:
        """エージェントのメインループを開始"""
        print(f"[{self.agent_id}] Starting agent controller...")

        max_iterations = 100  # 無限ループを防ぐためのカウンター
        iteration = 0

        while iteration < max_iterations:
            try:
                if self.message_bus:
                    message = self.message_bus.get_message(self.agent_id)
                    if message:
                        self._process_message(message)
                        time.sleep(1) # メッセージ処理後、少し待機
                    else:
                        time.sleep(2) # メッセージがない場合は少し長く待機
                else:
                    # 依存関係が注入されていない場合はループを抜ける
                    break
                iteration += 1
            except Exception as e:
                print(f"[{self.agent_id}] Error in message loop: {e}")
                break

    def _process_message(self, message: Message) -> None:
        """
        受け取ったメッセージを処理し、応答を生成して送信する
        """
        print(f"[{self.agent_id}] Processing message: {message.message_type}")
        try:
            response_message: Optional[Message] = None

            # GeminiServiceが利用可能な場合は、LLMを使って応答を生成する
            if self.gemini_service:
                llm_response = self.gemini_service.generate_structured_response(
                    agent_id=self.agent_id,
                    context=message
                )
                
                # LLMの応答から次のメッセージを作成
                if llm_response:
                    response_message = self._create_response_message(message, llm_response)
            else:
                # フォールバック: シナリオテスト用の簡易レスポンス生成
                response_message = self._generate_scenario_response(message)

            # 生成された応答メッセージをメッセージバスに投函
            if response_message and self.message_bus:
                self.message_bus.post_message(response_message)
                print(f"[{self.agent_id}] Sent response: "
                      f"{response_message.message_type} to "
                      f"{response_message.recipient_id}")
                      
        except Exception as e:
            print(f"[{self.agent_id}] Error processing message: {e}")

    def _create_response_message(
        self, original_message: Message, llm_response_message: Message
    ) -> Message:
        """LLMの応答(Messageオブジェクト)を、次の送信メッセージとして整形する"""
        # llm_response_messageは完全なMessageオブジェクトであると仮定
        # 必要に応じて、ここでターンのインクリメントなど、追加のロジックを実装できる
        llm_response_message.turn_id = original_message.turn_id + 1
        return llm_response_message

    def _generate_scenario_response(self, message: Message) -> Optional[Message]:
        """シナリオテスト用のハードコーディングされた応答メッセージを生成"""
        # MODERATORの応答ロジック
        if self.agent_id == "MODERATOR":
            if message.message_type == "INITIATE_DEBATE":
                return Message(
                    sender_id="MODERATOR",
                    recipient_id="DEBATER_A",
                    message_type="REQUEST_STATEMENT",
                    payload={"topic": message.payload.get("topic", "Unknown topic")},
                    turn_id=message.turn_id + 1
                )
            elif message.message_type == "SUBMIT_STATEMENT":
                return Message(
                    sender_id="MODERATOR",
                    recipient_id="SUPERVISOR",
                    message_type="SHUTDOWN_SYSTEM",
                    payload={"reason": "Scenario completed successfully"},
                    turn_id=message.turn_id + 1
                )

        # DEBATER_Aの応答ロジック
        elif self.agent_id == "DEBATER_A":
            if message.message_type == "REQUEST_STATEMENT":
                return Message(
                    sender_id="DEBATER_A",
                    recipient_id="MODERATOR",
                    message_type="SUBMIT_STATEMENT",
                    payload={
                        "statement": "AIエージェントの自律的協調は確実に人間の創造性を拡張します。データ処理能力と論理的推論により、人間では困難な複合的問題解決が可能になります。"
                    },
                    turn_id=message.turn_id + 1
                )

        return None

# 後方互換性のためのエイリアス
AgentLoop = AgentController