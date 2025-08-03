"""
ReAct Service - より高度なロジック実装（Green phase）
"""
import json
from typing import Optional, Dict, Any
from main.application.interfaces import ILLMService, IMessageBroker
from main.domain.models import Message


class ReActService:
    def __init__(self, llm_service: ILLMService,
                 message_broker: IMessageBroker = None):
        self.llm_service = llm_service
        self.message_broker = message_broker

    def think_and_act(self, agent_id: str, persona: str, history: list[Message]) -> Optional[Message]:
        """
        現在の文脈から次の行動を思考し、結果のメッセージを生成する
        """
        # 1. 履歴から最新のメッセージを取得
        context_message = history[-1] if history else None
        if not context_message:
            return None

        # 2. LLMに応答を生成させる（新しいインターフェース）
        response = self.llm_service.generate_response(
            agent_id, context_message)

        # 3. 既にMessageオブジェクトとして返されるので、そのまま返す
        return response

    def observe_think_act(self, agent_id: str) -> Optional[Message]:
        """
        完全なReActサイクル：観察→思考→行動
        """
        if not self.message_broker:
            return None

        # 観察: 新しいメッセージをチェック
        incoming_message = self.message_broker.get_message(agent_id)
        if not incoming_message:
            return None

        # 思考: LLMに状況を分析させる（新しいインターフェース）
        response = self.llm_service.generate_response(
            agent_id, incoming_message)

        # 行動: 既にMessageオブジェクトとして返されるのでそのまま返す
        return response

    def _build_react_prompt(
        self, agent_id: str, persona: str, history: list[Message]
    ) -> str:
        """思考を促すためのプロンプトを構築する"""
        prompt = f"""あなたは{agent_id}として行動してください。
ペルソナ: {persona}

これまでの議論の履歴:
"""
        for msg in history[-3:]:  # 最新3件のみ
            prompt += f"- {msg.sender_id}: {msg.payload}\n"

        prompt += """
次に取るべき行動を考えて、適切なメッセージを生成してください。
"""
        return prompt

    def _build_react_observation_prompt(
        self, agent_id: str, incoming_message: Message
    ) -> str:
        """観察に基づく思考プロンプトを構築"""
        return f"""
あなたは{agent_id}として行動してください。

観察（Observation）:
新しいメッセージを受信しました:
- 送信者: {incoming_message.sender_id}
- メッセージタイプ: {incoming_message.message_type}
- 内容: {incoming_message.payload}

思考（Thought）:
この状況を分析し、次に取るべき適切な行動を決定してください。

行動（Action）:
決定した行動を以下の形式で出力してください:

Action: post_message
Action Input: {{
    "recipient_id": "対象エージェントID",
    "message_type": "メッセージタイプ",
    "payload": {{適切なペイロード}}
}}
"""

    def _parse_response_to_message(
        self, agent_id: str, text: str
    ) -> Optional[Message]:
        """LLMの応答からメッセージを生成する"""
        # JSONアクションを抽出
        action_data = self._parse_action_from_response(text)
        if not action_data:
            return None

        return Message(
            sender_id=agent_id,
            recipient_id=action_data["recipient_id"],
            message_type=action_data["message_type"],
            payload=action_data["payload"],
            turn_id=1  # 仮のターンID
        )

    def _parse_action_from_response(
        self, response_text: str
    ) -> Optional[Dict[str, Any]]:
        """LLMの応答からアクションを抽出する（シンプル版）"""
        try:
            # ```json ブロックを探す
            if '```json' in response_text:
                start = response_text.find('```json')
                end = response_text.find('```', start + 7)
                if start != -1 and end != -1:
                    json_str = response_text[start+7:end].strip()
                    return json.loads(json_str)

            # 直接JSONを探す
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response_text[start:end].strip()
                return json.loads(json_str)

        except (json.JSONDecodeError, ValueError):
            pass

        return None
