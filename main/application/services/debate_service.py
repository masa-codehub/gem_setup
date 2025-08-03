"""
ディベート固有のアプリケーションサービス

TDD Green段階：ディベートのビジネスロジックをアプリケーション層で実装
ドメイン層の汎用モデルを使ってディベート機能を提供
"""

from main.domain.models import Message


class DebateService:
    """ディベートの進行管理を行うサービス"""

    def determine_next_action(self, last_message: Message) -> Message:
        """
        ディベートのステートマシンに基づき、次のメッセージを決定する
        （旧moderator.mdのロジックがここに入る）
        """
        if last_message.message_type == "START_SESSION":
            # セッション開始時の処理
            if last_message.payload.get("session_type") == "debate":
                return Message(
                    recipient_id="DEBATER_A",
                    sender_id="MODERATOR",
                    message_type="PROMPT_FOR_STATEMENT",
                    payload={
                        "topic": last_message.payload.get("topic"),
                        "phase": "statement",
                        "turn": 1
                    },
                    turn_id=last_message.turn_id + 1
                )

        elif last_message.message_type == "SUBMIT_RESPONSE":
            # 応答提出時の処理
            if last_message.payload.get("response_type") == "statement":
                if last_message.sender_id == "DEBATER_A":
                    # DEBATER_Aの発言後はDEBATER_Nの番
                    return Message(
                        recipient_id="DEBATER_N",
                        sender_id="MODERATOR",
                        message_type="PROMPT_FOR_STATEMENT",
                        payload={
                            "phase": "statement",
                            "turn": 2
                        },
                        turn_id=last_message.turn_id + 1
                    )

        # デフォルトの応答
        return Message(
            recipient_id="SYSTEM",
            sender_id="MODERATOR",
            message_type="SYSTEM_ERROR",
            payload={"error": "Unknown message type or state"},
            turn_id=last_message.turn_id + 1
        )
