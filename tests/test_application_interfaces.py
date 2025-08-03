#!/usr/bin/env python3
"""
アプリケーション層インターフェースのテスト
TDD: インターフェースから始める
"""

from main.entities.models import Message
from main.use_cases.interfaces import (
    IMessageBroker, ILLMService, IPromptRepository
)
from abc import ABC
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestInterfaces:
    """インターフェースのテスト"""

    def test_message_broker_interface(self):
        """IMessageBrokerが抽象クラスであることをテスト"""
        assert issubclass(IMessageBroker, ABC)

        # 抽象メソッドの存在確認
        abstract_methods = IMessageBroker.__abstractmethods__
        assert 'post_message' in abstract_methods
        assert 'get_message' in abstract_methods

    def test_llm_service_interface(self):
        """ILLMServiceが抽象クラスであることをテスト"""
        assert issubclass(ILLMService, ABC)

        # 抽象メソッドの存在確認
        abstract_methods = ILLMService.__abstractmethods__
        assert 'generate_response' in abstract_methods

    def test_prompt_repository_interface(self):
        """IPromptRepositoryが抽象クラスであることをテスト"""
        assert issubclass(IPromptRepository, ABC)

        # 抽象メソッドの存在確認
        abstract_methods = IPromptRepository.__abstractmethods__
        assert 'get_persona' in abstract_methods


class MockMessageBroker(IMessageBroker):
    """テスト用のモックメッセージブローカー"""

    def __init__(self):
        self.messages = []
        self.posted_messages = []

    def post_message(self, message: Message):
        self.posted_messages.append(message)

    def get_message(self, recipient_id: str) -> Message | None:
        for msg in self.messages:
            if msg.recipient_id == recipient_id:
                self.messages.remove(msg)
                return msg
        return None

    def add_message_for_test(self, message: Message):
        """テスト用のメッセージ追加"""
        self.messages.append(message)


class MockLLMService(ILLMService):
    """テスト用のモックLLMサービス"""

    def __init__(self, mock_response: str = "Mock AI response"):
        self.mock_response = mock_response
        self.last_prompt = None

    def generate_response(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.mock_response

    def generate_structured_response(
        self,
        agent_id: str,
        context,
        generation_config=None,
        model=None
    ):
        """新しい抽象メソッドの実装（テスト用）"""
        # テスト用のモックMessageオブジェクトを返す
        from main.entities.models import Message
        return Message(
            recipient_id="TEST_RECIPIENT",
            sender_id=agent_id,
            message_type="TEST_RESPONSE",
            payload={"content": self.mock_response},
            turn_id=context.turn_id + 1 if hasattr(context, 'turn_id') else 1
        )


class TestMockImplementations:
    """モック実装のテスト"""

    def test_mock_message_broker(self):
        """MockMessageBrokerが正しく動作することをテスト"""
        broker = MockMessageBroker()

        message = Message(
            recipient_id="DEBATER_A",
            sender_id="MODERATOR",
            message_type="PROMPT_FOR_STATEMENT",
            payload={"topic": "AI benefits"},
            turn_id=1
        )

        # メッセージ投稿のテスト
        broker.post_message(message)
        assert len(broker.posted_messages) == 1
        assert broker.posted_messages[0] == message

        # メッセージ追加と取得のテスト
        broker.add_message_for_test(message)
        retrieved = broker.get_message("DEBATER_A")
        assert retrieved == message

        # 存在しないメッセージの取得
        none_msg = broker.get_message("NONEXISTENT")
        assert none_msg is None

    def test_mock_llm_service(self):
        """MockLLMServiceが正しく動作することをテスト"""
        llm = MockLLMService("Test response")

        response = llm.generate_response("Test prompt")
        assert response == "Test response"
        assert llm.last_prompt == "Test prompt"
