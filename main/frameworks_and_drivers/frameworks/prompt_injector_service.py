"""
Prompt Injector Service - Green Phase Implementation
"""
from main.entities.models import Message, AgentID


class PromptInjectorService:
    """プロンプト注入サービス（テスト対応実装）"""

    def __init__(self, prompt_repository=None):
        """リポジトリを受け取るコンストラクタ"""
        self.prompt_repository = prompt_repository

    def build_prompt(self, agent_id: AgentID, context, history=None) -> str:
        """プロンプトを構築（テスト対応実装）"""
        if self.prompt_repository:
            persona = self.prompt_repository.get_persona(agent_id)
            base_prompt = f"{persona}"

            # contextの処理
            if hasattr(context, 'payload'):
                base_prompt += f" Context: {context.payload}"
            elif isinstance(context, dict):
                base_prompt += f" Context: {context}"
            else:
                base_prompt += f" Context: {context}"

            # historyの処理
            if history:
                history_text = " Previous messages: "
                for msg in history:
                    if hasattr(msg, 'payload') and 'message' in msg.payload:
                        history_text += f"{msg.payload['message']} "
                base_prompt += history_text

            return base_prompt
        return f"Agent {agent_id}: Please respond to the given context."

    def get_persona(self, agent_id: AgentID) -> str:
        """ペルソナを取得（簡易実装）"""
        if self.prompt_repository:
            return self.prompt_repository.get_persona(agent_id)
        return f"You are agent {agent_id}."
