"""
Prompt Injector Service - TDD Green Phase
プロンプト構築サービスの実装
"""
import os
from typing import Dict, Any


class PromptInjectorService:
    """プロンプト注入サービス - ペルソナと文脈からプロンプトを構築"""

    def __init__(self):
        """プロンプトインジェクターサービスを初期化"""
        self.config_dir = "/app/config"
        self.system_rules_file = "/app/config/debate_system.md"

    def build_prompt(self, agent_id: str, context: Dict[str, Any]) -> str:
        """エージェントのペルソナと文脈から、最終的なプロンプトを構築する"""
        persona = self.load_persona(agent_id)
        system_rules = self.load_system_rules()

        # メッセージから話題を抽出
        message = context.get('message')
        topic = ""
        if message and message.payload:
            topic = message.payload.get('topic', '')

        prompt = f"""
{system_rules}

Your Persona: {persona}

Current Context: Turn {context.get('current_turn', 1)}
Topic: {topic}
Message Type: {message.message_type if message else 'Unknown'}

Based on all of the above, what is your next action?
"""
        return prompt.strip()

    def load_persona(self, agent_id: str) -> str:
        """エージェントのペルソナを設定ファイルから読み込む"""
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
        config_file = os.path.join(self.config_dir, f"{agent_name}.md")

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            # デフォルトペルソナを返す
            return f"You are a helpful AI assistant acting as {agent_id}."

    def load_system_rules(self) -> str:
        """システムルールを読み込む"""
        try:
            with open(self.system_rules_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            # デフォルトルールを返す
            return "Follow professional communication standards."
