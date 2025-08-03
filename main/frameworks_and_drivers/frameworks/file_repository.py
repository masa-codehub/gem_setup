"""
ファイルベースのプロンプトリポジトリ実装
IPromptRepositoryインターフェースの具体的な実装
"""

import os
from main.use_cases.interfaces import IPromptRepository
from main.entities.models import AgentID


class FileBasedPromptRepository(IPromptRepository):
    """ファイルシステムベースのプロンプト・ペルソナ管理"""

    def __init__(self, config_dir: str = None):
        """
        Args:
            config_dir: 設定ファイルディレクトリのパス。Noneの場合は./config
        """
        self.config_dir = config_dir or "./config"

    def get_persona(self, agent_id: AgentID) -> str:
        """エージェントのペルソナを取得する"""
        persona_file = os.path.join(
            self.config_dir, f"{agent_id.lower()}.md"
        )

        try:
            with open(persona_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            return ""
        except Exception:
            return ""
