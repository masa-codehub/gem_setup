"""
新しい抽象化されたドメイン層モデル - TDD Green段階

Kent BeckのTDD思想に従い、テストを通すための最小限の実装。
ディベート固有の概念を排除し、汎用的なエージェント連携プラットフォームの基本要素のみを残す。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import time

# --- Generic Type Definitions ---
AgentID = str  # 具体的なLiteralから汎用的なstringへ変更
MessageType = str  # 具体的なLiteralから汎用的なstringへ変更


def _default_timestamp():
    """デフォルトタイムスタンプ生成"""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# --- Core Domain Entities ---

@dataclass
class Agent:
    """プラットフォームにおけるエージェントの基本定義"""
    agent_id: AgentID
    role: str  # Roleは具体的なアプリケーションが定義するため、ドメイン層では汎用的な文字列とする


@dataclass
class Message:
    """エージェント間の通信に使われる汎用メッセージ"""
    recipient_id: AgentID
    sender_id: AgentID
    message_type: MessageType  # 'SUBMIT_STATEMENT'のような具体的な型はアプリケーション層で解釈
    payload: Dict[str, Any]  # アプリケーション固有のデータは全てここに格納
    turn_id: int
    timestamp: str = field(default_factory=_default_timestamp)

    def __post_init__(self):
        """メッセージ作成後の検証"""
        if not self.payload:
            self.payload = {}


@dataclass
class Task:
    """エージェントが処理する作業単位"""
    task_id: str
    title: str
    description: str
    status: str  # 例: 'TODO', 'IN_PROGRESS', 'DONE'
    assignee_id: AgentID
    dependencies: List[str] = field(default_factory=list)


@dataclass
class Session:
    """エージェントたちが協調作業を行うセッション"""
    session_id: str
    objective: str  # プロジェクト全体の目標
    participants: List[AgentID]
    status: str  # 例: 'RUNNING', 'COMPLETED', 'FAILED'
