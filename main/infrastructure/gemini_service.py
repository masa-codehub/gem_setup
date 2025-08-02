"""
Geminiサービスの実装
ILLMServiceインターフェースの具体的な実装
"""

import subprocess
from main.application.interfaces import ILLMService


class GeminiService(ILLMService):
    """Gemini APIを使ったLLMサービス"""

    def __init__(self, timeout: int = 90):
        """
        Args:
            timeout: API呼び出しのタイムアウト時間（秒）
        """
        self.timeout = timeout

    def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        """プロンプトに対する応答を生成する（ダミー実装）"""

        # MODERATORの場合：DEBATER_Aに議論開始を促す
        if "MODERATOR" in prompt and "PROMPT_FOR_STATEMENT" in prompt:
            return '''```json
{
    "recipient_id": "DEBATER_A",
    "message_type": "PROMPT_FOR_STATEMENT", 
    "payload": {
        "topic": "The impact of artificial intelligence on humanity",
        "instructions": "Please provide your opening statement supporting the positive impact of AI on humanity. You have 300 words."
    }
}
```'''

        # DEBATER_Aの場合：MODERATORに立論を送信
        if "DEBATER_A" in prompt and ("PROMPT_FOR_STATEMENT" in prompt or "opening statement" in prompt):
            return '''```json
{
    "recipient_id": "MODERATOR",
    "message_type": "SUBMIT_STATEMENT",
    "payload": {
        "statement": "I argue that AI has tremendous positive potential for humanity. AI can solve complex problems in healthcare, help us understand climate change, and enhance human capabilities rather than replace them. The key is responsible development and deployment."
    }
}
```'''

        # デフォルト応答
        return '''```json
{
    "recipient_id": "SYSTEM",
    "message_type": "SYSTEM_ERROR",
    "payload": {
        "error": "No appropriate response pattern found"
    }
}
```'''
