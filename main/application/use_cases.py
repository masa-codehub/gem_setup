"""
アプリケーション層のユースケース
ビジネスロジックの核心部分
"""

import re
from main.application.interfaces import (
    IMessageBroker, ILLMService, IPromptRepository,
    IDebateHistoryService
)
from main.domain.models import Message, AgentID


class SubmitStatementUseCase:
    """立論提出のユースケース"""

    def __init__(self, llm_service: ILLMService,
                 message_broker: IMessageBroker,
                 prompt_repository: IPromptRepository):
        self.llm_service = llm_service
        self.message_broker = message_broker
        self.prompt_repository = prompt_repository

    def execute(self, topic: str, sender_id: AgentID, turn_id: int) -> None:
        """立論を生成して提出する"""
        # ペルソナを取得
        persona = self.prompt_repository.get_persona(sender_id)

        # プロンプト生成
        prompt = self._build_statement_prompt(persona, topic, sender_id)

        # LLMから応答生成
        statement_content = self.llm_service.generate_response(prompt)

        # メッセージ作成と送信
        response_message = Message(
            recipient_id="MODERATOR",
            sender_id=sender_id,
            message_type="SUBMIT_STATEMENT",
            payload={"content": statement_content},
            turn_id=turn_id + 1
        )

        self.message_broker.post_message(response_message)

    def _build_statement_prompt(self, persona: str, topic: str,
                                sender_id: AgentID) -> str:
        """立論用のプロンプトを構築"""
        position = self._get_position_for_agent(sender_id)

        return f"""あなたは{sender_id}として討論に参加します。

{persona}

討論トピック：{topic}

あなたの立場：{position}

あなたの開始声明を300文字程度で述べてください。
論理的で説得力のある議論を展開してください。"""

    def _get_position_for_agent(self, agent_id: AgentID) -> str:
        """エージェントの立場を取得"""
        if agent_id == "DEBATER_A":
            return "人工知能の発達は人類にとって有益である"
        elif agent_id == "DEBATER_N":
            return "人工知能の発達は人類にとって有害である"
        else:
            return "中立的な立場"


class SubmitRebuttalUseCase:
    """反駁提出のユースケース"""

    def __init__(self, llm_service: ILLMService,
                 message_broker: IMessageBroker,
                 prompt_repository: IPromptRepository,
                 history_service: IDebateHistoryService):
        self.llm_service = llm_service
        self.message_broker = message_broker
        self.prompt_repository = prompt_repository
        self.history_service = history_service

    def execute(self, topic: str, sender_id: AgentID, turn_id: int) -> None:
        """反駁を生成して提出する"""
        # ペルソナと履歴を取得
        persona = self.prompt_repository.get_persona(sender_id)
        history = self.history_service.get_debate_history()

        # プロンプト生成
        prompt = self._build_rebuttal_prompt(
            persona, topic, history, sender_id
        )

        # LLMから応答生成
        rebuttal_content = self.llm_service.generate_response(prompt)

        # メッセージ作成と送信
        response_message = Message(
            recipient_id="MODERATOR",
            sender_id=sender_id,
            message_type="SUBMIT_REBUTTAL",
            payload={"content": rebuttal_content},
            turn_id=turn_id + 1
        )

        self.message_broker.post_message(response_message)

    def _build_rebuttal_prompt(self, persona: str, topic: str,
                               history: list, sender_id: AgentID) -> str:
        """反駁用のプロンプトを構築"""
        history_text = "\n\n".join(
            [f"{h['sender']}: {h['content']}" for h in history]
        )

        return f"""あなたは{sender_id}として討論を続けます。

{persona}

討論トピック：{topic}

これまでの議論：
{history_text}

上記の相手の主張を踏まえ、あなたの反駁を300文字程度で述べてください。
相手の論点に対する具体的な反論を含めてください。"""


class SubmitJudgementUseCase:
    """判定提出のユースケース"""

    def __init__(self, llm_service: ILLMService,
                 message_broker: IMessageBroker,
                 prompt_repository: IPromptRepository,
                 history_service: IDebateHistoryService):
        self.llm_service = llm_service
        self.message_broker = message_broker
        self.prompt_repository = prompt_repository
        self.history_service = history_service

    def execute(self, topic: str, sender_id: AgentID, turn_id: int) -> None:
        """判定を生成して提出する"""
        # ペルソナと履歴を取得
        persona = self.prompt_repository.get_persona(sender_id)
        history = self.history_service.get_debate_history()

        # プロンプト生成
        prompt = self._build_judgement_prompt(
            persona, topic, history, sender_id
        )

        # LLMから応答生成
        judgement_content = self.llm_service.generate_response(prompt)

        # スコアを抽出
        scores = self._extract_scores(judgement_content)

        # メッセージ作成と送信
        response_message = Message(
            recipient_id="MODERATOR",
            sender_id=sender_id,
            message_type="SUBMIT_JUDGEMENT",
            payload={
                "scores": scores,
                "reasoning": judgement_content
            },
            turn_id=turn_id + 1
        )

        self.message_broker.post_message(response_message)

    def _build_judgement_prompt(self, persona: str, topic: str,
                                history: list, sender_id: AgentID) -> str:
        """判定用のプロンプトを構築"""
        history_text = "\n\n".join(
            [f"{h['sender']}: {h['content']}" for h in history]
        )

        return f"""あなたは{sender_id}として討論の判定を行います。

{persona}

討論トピック：{topic}

完全な討論内容：
{history_text}

DEBATER_A（有益派）とDEBATER_N（有害派）の討論を以下の観点で評価してください：

## 評価項目（各10点満点）

### 1. 論理性と一貫性
### 2. 証拠と根拠の充実度
### 3. 反駁の効果性
### 4. 最終弁論の説得力
### 5. 総合評価

## 採点結果

**DEBATER_A 採点:**
- 論理性と一貫性: X/10点
- 証拠と根拠: X/10点
- 反駁の効果性: X/10点
- 最終弁論: X/10点
- 総合評価: X/10点
- **合計: XX/50点**

**DEBATER_N 採点:**
- 論理性と一貫性: X/10点
- 証拠と根拠: X/10点
- 反駁の効果性: X/10点
- 最終弁論: X/10点
- 総合評価: X/10点
- **合計: XX/50点**

## 判定理由
両者の議論を比較し、採点理由を300文字程度で詳しく説明してください。"""

    def _extract_scores(self, judgement_text: str) -> dict:
        """判定テキストからスコアを抽出"""
        # DEBATERのスコア抽出（DOTALLフラグで改行をまたいでマッチ）
        total_a_match = re.search(
            r'DEBATER_A.*?合計:\s*(\d+)', judgement_text, re.DOTALL
        )
        total_n_match = re.search(
            r'DEBATER_N.*?合計:\s*(\d+)', judgement_text, re.DOTALL
        )

        a_score = int(total_a_match.group(1)) if total_a_match else 35
        n_score = int(total_n_match.group(1)) if total_n_match else 35

        return {
            "debater_a": a_score,
            "debater_n": n_score
        }
