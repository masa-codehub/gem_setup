"""
アプリケーション層のインターフェース定義
依存性逆転の原則により外部サービスとの窓口を抽象化
"""

from abc import ABC, abstractmethod
from typing import Optional
from main.entities.models import Message, AgentID


class IMessageBroker(ABC):
    """メッセージブローカーのインターフェース"""

    @abstractmethod
    def post_message(self, message: Message) -> None:
        """メッセージを送信する"""
        pass

    @abstractmethod
    def get_message(self, recipient_id: AgentID) -> Optional[Message]:
        """指定した受信者宛のメッセージを取得する"""
        pass


class ILLMService(ABC):
    """LLM（大規模言語モデル）サービスのインターフェース"""

    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """プロンプトに対する応答を生成する"""
        pass


class IPromptRepository(ABC):
    """プロンプト・ペルソナ管理のインターフェース"""

    @abstractmethod
    def get_persona(self, agent_id: AgentID) -> str:
        """エージェントのペルソナを取得する"""
        pass


class IDebateHistoryService(ABC):
    """討論履歴管理のインターフェース"""

    @abstractmethod
    def get_debate_history(self) -> list:
        """これまでの討論履歴を取得する"""
        pass


class IErrorNotificationService(ABC):
    """エラー通知サービスのインターフェース"""

    @abstractmethod
    def notify_system_error(self, error_message: str,
                            agent_id: AgentID) -> None:
        """システムエラーを通知する"""
        pass
