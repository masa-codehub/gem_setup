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
        """プロンプトに対する応答を生成する"""
        try:
            cmd = ["gemini"]
            if system_prompt:
                cmd.extend(["-s", system_prompt])
            cmd.extend(["-p", prompt])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout
            )

            if result.returncode == 0:
                response = result.stdout.strip()
                return response
            else:
                error_msg = result.stderr.strip()
                raise RuntimeError(f"Gemini API error: {error_msg}")

        except subprocess.TimeoutExpired:
            raise RuntimeError("Gemini API timeout")
        except FileNotFoundError:
            raise RuntimeError("Gemini command not available")
