"""
アプリケーション層のディベート固有モデル

TDD Green段階：ディベートに特化したモデルをアプリケーション層に配置
ドメイン層の汎用モデルを組み合わせてディベート機能を実現
"""

from dataclasses import dataclass, field
from typing import List
import time
from main.entities.models import Session, AgentID


def _default_timestamp():
    """デフォルトタイムスタンプ生成"""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class DebateSession:
    """ディベート専用のセッション - ドメインのSessionを拡張"""
    base_session: Session
    topic: str
    current_phase: str  # "statement", "rebuttal", "closing_statement", etc.


@dataclass
class DebateStatement:
    """ディベートの発言"""
    author_id: AgentID
    content: str
    statement_type: str  # "opening", "rebuttal", "closing"
    turn_number: int
    created_at: str = field(default_factory=_default_timestamp)


@dataclass
class JudgementScore:
    """判定スコア"""
    debater_a_score: int
    debater_n_score: int
    judge_id: AgentID
    reasoning: str

    def __post_init__(self):
        """スコア検証"""
        if not (0 <= self.debater_a_score <= 50):
            raise ValueError("DEBATER_A score must be between 0 and 50")
        if not (0 <= self.debater_n_score <= 50):
            raise ValueError("DEBATER_N score must be between 0 and 50")


@dataclass
class DebatePhase:
    """討論の進行フェーズ"""
    phase: str
    participants: List[AgentID]
    completed_participants: List[AgentID] = field(default_factory=list)

    def mark_participant_done(self, participant_id: AgentID):
        """参加者の完了をマーク"""
        if (participant_id in self.participants and
                participant_id not in self.completed_participants):
            self.completed_participants.append(participant_id)

    def is_complete(self) -> bool:
        """フェーズが完了しているかチェック"""
        return len(self.completed_participants) == len(self.participants)

    def get_remaining_participants(self) -> List[AgentID]:
        """未完了の参加者を取得"""
        return [p for p in self.participants
                if p not in self.completed_participants]
