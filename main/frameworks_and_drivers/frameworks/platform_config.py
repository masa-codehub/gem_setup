"""
プラットフォーム設定管理クラス

設定ファイルの読み込みと、パスの解決ロジックをカプセル化する
Kent BeckのTDD思想に従い、テストファーストで実装
"""

import os
import re
import yaml
from typing import Dict, Any


class PlatformConfig:
    """プラットフォーム設定管理クラス"""

    def __init__(self, config_path: str):
        """
        設定ファイルを読み込んでPlatformConfigオブジェクトを初期化

        Args:
            config_path: 設定ファイル(YAML)のパス

        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Configuration file not found at: {config_path}"
            )

        self.config_path = config_path

        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

        self._resolve_paths()

    def _resolve_paths(self):
        """設定ファイル内の相対パスを絶対パスに解決する"""
        platform_config = self._config.get('platform_config', {})

        # data_storage_pathの解決
        base_path = platform_config.get('data_storage_path', './runs')
        base_path = self._expand_environment_variables(base_path)

        if not os.path.isabs(base_path):
            # プロジェクトルートからの相対パスとして扱う
            base_path = os.path.abspath(base_path)

        # ディレクトリが存在しない場合は作成
        os.makedirs(base_path, exist_ok=True)
        self.data_storage_path = base_path

        # message_db_pathの解決（ディレクトリパス）
        db_dir = platform_config.get('message_db_path', './')
        db_dir = self._expand_environment_variables(db_dir)

        if os.path.isabs(db_dir):
            self.message_db_path = db_dir
        else:
            self.message_db_path = os.path.join(
                self.data_storage_path, db_dir
            )

        # ディレクトリが存在しない場合は作成
        os.makedirs(self.message_db_path, exist_ok=True)

        # agent_config_pathの解決
        self.agent_config_path = platform_config.get(
            'agent_config_path', './config'
        )
        self.agent_config_path = self._expand_environment_variables(
            self.agent_config_path
        )

    def _expand_environment_variables(self, value: str) -> str:
        """
        環境変数の展開を行う

        ${VAR_NAME:-default_value} 形式をサポート
        """
        def replace_env_var(match):
            var_with_default = match.group(1)
            if ':-' in var_with_default:
                var_name, default_value = var_with_default.split(':-', 1)
                return os.environ.get(var_name, default_value)
            else:
                return os.environ.get(var_with_default, match.group(0))

        # ${VAR_NAME:-default} または ${VAR_NAME} パターンにマッチ
        pattern = r'\$\{([^}]+)\}'
        return re.sub(pattern, replace_env_var, value)

    @property
    def project_definition(self) -> Dict[str, Any]:
        """プロジェクト定義の全体を取得"""
        return self._config

    def get_agent_config_by_id(self, agent_id: str) -> Dict[str, Any]:
        """
        指定されたエージェントIDの設定を取得

        Args:
            agent_id: エージェントID

        Returns:
            エージェント設定辞書、見つからない場合は空辞書
        """
        agents = self._config.get('agents', [])
        for agent in agents:
            if agent.get('id') == agent_id:
                return agent
        return {}

    def get_message_bus_config(self) -> Dict[str, Any]:
        """メッセージバス設定を取得"""
        return self._config.get('message_bus', {})

    def get_initial_task_config(self) -> Dict[str, Any]:
        """初期タスク設定を取得"""
        return self._config.get('initial_task', {})

    def get_platform_config(self) -> Dict[str, Any]:
        """プラットフォーム設定を取得"""
        return self._config.get('platform', {})

    def get_message_db_file_path(self, db_filename: str = "messages.db") -> str:
        """
        メッセージデータベースファイルの完全パスを取得

        Args:
            db_filename: データベースファイル名（デフォルト: messages.db）

        Returns:
            完全なデータベースファイルパス
        """
        return os.path.join(self.message_db_path, db_filename)
