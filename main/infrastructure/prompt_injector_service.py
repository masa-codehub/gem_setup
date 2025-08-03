"""
Prompt Injector Service - TDD Green Phase
プロンプト構築サービスの実装（リファクタリング版）
"""
from typing import List, Optional
from main.application.interfaces import IPromptRepository
from main.domain.models import Message


class PromptInjectorService:
    """プロンプト注入サービス - ペルソナと文脈からプロンプトを構築"""

    def __init__(self, prompt_repository: IPromptRepository):
        """プロンプトインジェクターサービスを初期化"""
        self.prompt_repository = prompt_repository
        self.system_rules_file = "/app/config/debate_system.md"

    def build_prompt(self, agent_id: str, context: Message,
                     history: Optional[List[Message]] = None) -> str:
        """エージェントのペルソナと文脈から、最終的なプロンプトを構築する"""
        persona = self.prompt_repository.get_persona(agent_id)
        system_rules = self.load_system_rules()

        # メッセージから情報を抽出
        payload = context.payload or {}

        # 履歴がある場合はフォーマット
        history_text = ""
        if history:
            history_text = "\n\nConversation History:\n"
            for msg in history:
                history_text += f"- {msg.sender_id} -> {msg.recipient_id}: "
                history_text += f"{msg.message_type} - {msg.payload}\n"

        prompt = f"""
{system_rules}

Your Persona: {persona}

Current Context:
- Turn: {context.turn_id}
- Message Type: {context.message_type}
- From: {context.sender_id}
- To: {context.recipient_id}
- Payload: {payload}
{history_text}

Based on all of the above, what is your next action?
"""
        return prompt.strip()

    def load_system_rules(self) -> str:
        """システムルールを読み込む"""
        try:
            with open(self.system_rules_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            # デフォルトルールを返す
            return "Follow professional communication standards."
