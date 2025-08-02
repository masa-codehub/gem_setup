"""
ドメイン層 - ディベートシステムの核となるデータモデル
ビジネスルールとデータ構造を純粋な形で定義
"""

from dataclasses import dataclass, field
from typing import Literal, List, Dict, Optional
import time

# 型定義
AgentID = Literal[
    "DEBATER_A", "DEBATER_N", "MODERATOR",
    "JUDGE_L", "JUDGE_E", "JUDGE_R", "ANALYST"
]
MessageType = Literal[
    "PROMPT_FOR_STATEMENT", "SUBMIT_STATEMENT",
    "PROMPT_FOR_REBUTTAL", "SUBMIT_REBUTTAL",
    "PROMPT_FOR_CLOSING_STATEMENT", "SUBMIT_CLOSING_STATEMENT",
    "REQUEST_JUDGEMENT", "SUBMIT_JUDGEMENT",
    "DEBATE_RESULTS", "END_DEBATE", "SYSTEM_ERROR"
]
Role = Literal["debater", "judge", "moderator", "analyst"]
Phase = Literal[
    "statement", "rebuttal", "closing_statement",
    "judgement", "analysis", "completed"
]


def _default_timestamp():
    """デフォルトタイムスタンプ生成"""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class Message:
    """ディベートシステムにおけるメッセージ"""
    recipient_id: AgentID
    sender_id: AgentID
    message_type: MessageType
    payload: Dict
    turn_id: int
    timestamp: str = field(default_factory=_default_timestamp)

    def __post_init__(self):
        """メッセージ作成後の検証"""
        if not self.payload:
            self.payload = {}


@dataclass
class Statement:
    """討論における発言"""
    author_id: AgentID
    content: str
    created_at: str = field(default_factory=_default_timestamp)

    def __post_init__(self):
        """発言作成後の検証"""
        if not self.content.strip():
            raise ValueError("Statement content cannot be empty")


@dataclass
class Agent:
    """ディベート参加者"""
    agent_id: AgentID
    role: Role
    persona: str = ""

    def __post_init__(self):
        """エージェント作成後の検証"""
        if self.role not in ["debater", "judge", "moderator", "analyst"]:
            raise ValueError(f"Invalid role: {self.role}")


@dataclass
class DebatePhase:
    """討論の進行フェーズ"""
    phase: Phase
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
class DebateSession:
    """討論セッション全体"""
    topic: str
    session_id: str
    current_phase: Phase = "statement"
    participants: List[AgentID] = field(default_factory=list)
    statements: List[Statement] = field(default_factory=list)
    judgements: List[JudgementScore] = field(default_factory=list)
    created_at: str = field(default_factory=_default_timestamp)

    def add_statement(self, statement: Statement):
        """発言を追加"""
        self.statements.append(statement)

    def add_judgement(self, judgement: JudgementScore):
        """判定を追加"""
        self.judgements.append(judgement)

    def get_final_scores(self) -> Optional[Dict[str, float]]:
        """最終スコアを計算"""
        if not self.judgements:
            return None

        total_a = sum(j.debater_a_score for j in self.judgements)
        total_n = sum(j.debater_n_score for j in self.judgements)
        count = len(self.judgements)

        winner = ("DEBATER_A" if total_a > total_n else
                  "DEBATER_N" if total_n > total_a else "DRAW")

        return {
            "debater_a_average": total_a / count,
            "debater_n_average": total_n / count,
            "winner": winner
        }
