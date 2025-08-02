#!/usr/bin/env python3
"""
ReActベースのモデレーターエージェント
ディベートシステムのルールに基づいて自律的にディベートを進行管理する
"""

import os
import time
import json
import sys
from typing import Dict, Any, Optional
import message_broker


def post_message_tool(recipient_id: str, message_json: str) -> str:
    """
    指定したエージェントにメッセージを送信します。

    Args:
        recipient_id: 送信先のエージェントID (例: 'DEBATER_A', 'JUDGE_L')
        message_json: 送信するメッセージのJSON文字列

    Returns:
        送信結果のメッセージ
    """
    try:
        message_body = json.loads(message_json)
        message_broker.post_message(recipient_id, message_body)
        return f"Message successfully sent to {recipient_id}."
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON format - {e}"
    except Exception as e:
        return f"Error: Failed to send message - {e}"


def get_my_message_tool(my_id: str) -> str:
    """
    自分宛の未読メッセージを取得します。

    Args:
        my_id: 自分のエージェントID

    Returns:
        メッセージのJSON文字列、または "No new messages."
    """
    try:
        message = message_broker.get_message(my_id)
        if message:
            return json.dumps(message, ensure_ascii=False)
        return "No new messages."
    except Exception as e:
        return f"Error: Failed to get message - {e}"


def get_debate_status_tool() -> str:
    """
    現在のディベートの状況を取得します。

    Returns:
        ディベートの進行状況に関する情報
    """
    try:
        stats = message_broker.get_statistics()
        return json.dumps(stats, ensure_ascii=False)
    except Exception as e:
        return f"Error: Failed to get debate status - {e}"


# ツールの定義（ReActライブラリが使用できない場合の代替実装）
AVAILABLE_TOOLS = {
    "post_message": post_message_tool,
    "get_my_message": get_my_message_tool,
    "get_debate_status": get_debate_status_tool
}


class SimpleReActModerator:
    """
    シンプルなReAct風のモデレーター実装
    本来はGeminiのReActライブラリを使用しますが、利用できない場合の代替実装
    """

    def __init__(self, agent_id: str = "MODERATOR"):
        self.agent_id = agent_id
        self.debate_state = {
            "current_phase": "WAITING_FOR_START",
            "received_statements": {"DEBATER_A": False, "DEBATER_N": False},
            "received_rebuttals": {"DEBATER_A": False, "DEBATER_N": False},
            "received_closing": {"DEBATER_A": False, "DEBATER_N": False},
            "received_judgments": {"JUDGE_L": False, "JUDGE_E": False, "JUDGE_R": False},
            "turn_id": 0
        }

        # 設定ファイルの読み込み
        self.load_configurations()

    def load_configurations(self):
        """設定ファイルを読み込む"""
        try:
            with open("./config/debate_system.md", "r", encoding="utf-8") as f:
                self.debate_rules = f.read()

            with open("./config/moderator.md", "r", encoding="utf-8") as f:
                self.moderator_persona = f.read()

            print(f"[{self.agent_id}] Configuration files loaded successfully")
        except Exception as e:
            print(f"[{self.agent_id}] Error loading configurations: {e}")
            self.debate_rules = ""
            self.moderator_persona = ""

    def think_and_act(self, context: str = "") -> Optional[Dict[str, Any]]:
        """
        現在の状況を分析し、適切なアクションを決定・実行する

        Args:
            context: 追加のコンテキスト情報

        Returns:
            実行したアクションの結果
        """
        # 1. 観察（Observation）- 新しいメッセージをチェック
        message_result = get_my_message_tool(self.agent_id)

        if message_result != "No new messages.":
            try:
                new_message = json.loads(message_result)
                print(
                    f"[{self.agent_id}] 📨 New message: {new_message.get('message_type', 'UNKNOWN')}")

                # 2. 思考（Reasoning）- メッセージの種類に基づいて次のアクションを決定
                action = self.reason_next_action(new_message)

                if action:
                    # 3. 行動（Acting）- 決定したアクションを実行
                    result = self.execute_action(action)
                    print(
                        f"[{self.agent_id}] ✅ Action executed: {action['type']}")
                    return result

            except json.JSONDecodeError as e:
                print(f"[{self.agent_id}] ❌ Failed to parse message: {e}")

        return None

    def reason_next_action(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        受信したメッセージに基づいて次のアクションを決定する

        Args:
            message: 受信したメッセージ

        Returns:
            実行すべきアクションの辞書、またはNone
        """
        msg_type = message.get("message_type")
        sender = message.get("sender_id")

        print(
            f"[{self.agent_id}] 🤔 Reasoning for message type: {msg_type} from {sender}")

        if msg_type == "START_DEBATE":
            self.debate_state["current_phase"] = "OPENING_STATEMENTS"
            return {
                "type": "send_prompt",
                "recipient": "DEBATER_A",
                "message_type": "PROMPT_FOR_STATEMENT",
                "content": "Please provide your opening statement for the affirmative side."
            }

        elif msg_type == "SUBMIT_STATEMENT":
            if sender == "DEBATER_A" and not self.debate_state["received_statements"]["DEBATER_A"]:
                self.debate_state["received_statements"]["DEBATER_A"] = True
                return {
                    "type": "multi_send",
                    "actions": [
                        {
                            "recipient": "DEBATER_N",
                            "message_type": "STATEMENT_FOR_REVIEW",
                            "content": f"DEBATER_A's statement: {message.get('payload', {}).get('content', '')}"
                        },
                        {
                            "recipient": "DEBATER_N",
                            "message_type": "PROMPT_FOR_STATEMENT",
                            "content": "Please provide your opening statement for the negative side."
                        }
                    ]
                }

            elif sender == "DEBATER_N" and not self.debate_state["received_statements"]["DEBATER_N"]:
                self.debate_state["received_statements"]["DEBATER_N"] = True
                self.debate_state["current_phase"] = "REBUTTALS"
                return {
                    "type": "multi_send",
                    "actions": [
                        {
                            "recipient": "DEBATER_A",
                            "message_type": "STATEMENT_FOR_REVIEW",
                            "content": f"DEBATER_N's statement: {message.get('payload', {}).get('content', '')}"
                        },
                        {
                            "recipient": "DEBATER_A",
                            "message_type": "PROMPT_FOR_REBUTTAL",
                            "content": "Please provide your rebuttal to the negative side's arguments."
                        }
                    ]
                }

        elif msg_type == "SUBMIT_REBUTTAL":
            if sender == "DEBATER_A" and not self.debate_state["received_rebuttals"]["DEBATER_A"]:
                self.debate_state["received_rebuttals"]["DEBATER_A"] = True
                return {
                    "type": "multi_send",
                    "actions": [
                        {
                            "recipient": "DEBATER_N",
                            "message_type": "REBUTTAL_FOR_REVIEW",
                            "content": f"DEBATER_A's rebuttal: {message.get('payload', {}).get('content', '')}"
                        },
                        {
                            "recipient": "DEBATER_N",
                            "message_type": "PROMPT_FOR_REBUTTAL",
                            "content": "Please provide your rebuttal to the affirmative side's arguments."
                        }
                    ]
                }

            elif sender == "DEBATER_N" and not self.debate_state["received_rebuttals"]["DEBATER_N"]:
                self.debate_state["received_rebuttals"]["DEBATER_N"] = True
                self.debate_state["current_phase"] = "CLOSING_STATEMENTS"
                return {
                    "type": "multi_send",
                    "actions": [
                        {
                            "recipient": "DEBATER_A",
                            "message_type": "REBUTTAL_FOR_REVIEW",
                            "content": f"DEBATER_N's rebuttal: {message.get('payload', {}).get('content', '')}"
                        },
                        {
                            "recipient": "DEBATER_A",
                            "message_type": "PROMPT_FOR_CLOSING_STATEMENT",
                            "content": "Please provide your closing statement."
                        }
                    ]
                }

        elif msg_type == "SUBMIT_CLOSING_STATEMENT":
            if sender == "DEBATER_A" and not self.debate_state["received_closing"]["DEBATER_A"]:
                self.debate_state["received_closing"]["DEBATER_A"] = True
                return {
                    "type": "multi_send",
                    "actions": [
                        {
                            "recipient": "DEBATER_N",
                            "message_type": "CLOSING_STATEMENT_FOR_REVIEW",
                            "content": f"DEBATER_A's closing: {message.get('payload', {}).get('content', '')}"
                        },
                        {
                            "recipient": "DEBATER_N",
                            "message_type": "PROMPT_FOR_CLOSING_STATEMENT",
                            "content": "Please provide your closing statement."
                        }
                    ]
                }

            elif sender == "DEBATER_N" and not self.debate_state["received_closing"]["DEBATER_N"]:
                self.debate_state["received_closing"]["DEBATER_N"] = True
                self.debate_state["current_phase"] = "JUDGMENT"
                return {
                    "type": "multi_send",
                    "actions": [
                        {
                            "recipient": "JUDGE_L",
                            "message_type": "REQUEST_JUDGEMENT",
                            "content": "Please provide your judgment on this debate."
                        },
                        {
                            "recipient": "JUDGE_E",
                            "message_type": "REQUEST_JUDGEMENT",
                            "content": "Please provide your judgment on this debate."
                        },
                        {
                            "recipient": "JUDGE_R",
                            "message_type": "REQUEST_JUDGEMENT",
                            "content": "Please provide your judgment on this debate."
                        }
                    ]
                }

        elif msg_type == "SUBMIT_JUDGEMENT":
            if sender in self.debate_state["received_judgments"]:
                self.debate_state["received_judgments"][sender] = True

                # 全ジャッジの判定が揃ったかチェック
                if all(self.debate_state["received_judgments"].values()):
                    self.debate_state["current_phase"] = "COMPLETE"
                    return {
                        "type": "end_debate",
                        "message": "All judgments received. Debate complete."
                    }

        return None

    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        決定されたアクションを実行する

        Args:
            action: 実行するアクションの詳細

        Returns:
            実行結果
        """
        action_type = action.get("type")
        self.debate_state["turn_id"] += 1

        if action_type == "send_prompt":
            return self._send_single_message(action)

        elif action_type == "multi_send":
            results = []
            for sub_action in action.get("actions", []):
                result = self._send_single_message(sub_action)
                results.append(result)
            return {"type": "multi_send", "results": results}

        elif action_type == "end_debate":
            return self._end_debate(action.get("message", "Debate ended."))

        return {"error": f"Unknown action type: {action_type}"}

    def _send_single_message(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """単一のメッセージを送信する"""
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        message = {
            "turn_id": self.debate_state["turn_id"],
            "timestamp": timestamp,
            "sender_id": self.agent_id,
            "recipient_id": action["recipient"],
            "message_type": action["message_type"],
            "payload": {
                "content": action["content"]
            }
        }

        result = post_message_tool(
            action["recipient"], json.dumps(message, ensure_ascii=False))
        return {"recipient": action["recipient"], "result": result}

    def _end_debate(self, message: str) -> Dict[str, Any]:
        """ディベートを終了する"""
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        end_message = {
            "turn_id": self.debate_state["turn_id"],
            "timestamp": timestamp,
            "sender_id": self.agent_id,
            "recipient_id": "ALL",
            "message_type": "END_DEBATE",
            "payload": {
                "content": message,
                "final_state": self.debate_state
            }
        }

        # 全エージェントに終了メッセージを送信
        agents = ["DEBATER_A", "DEBATER_N", "JUDGE_L",
                  "JUDGE_E", "JUDGE_R", "ANALYST"]
        results = []

        for agent in agents:
            result = post_message_tool(
                agent, json.dumps(end_message, ensure_ascii=False))
            results.append({"agent": agent, "result": result})

        return {"type": "end_debate", "results": results}


def main_loop():
    """ReActモデレーターのメインループ"""
    agent_id = os.environ.get("AGENT_ID", "MODERATOR")

    if agent_id != "MODERATOR":
        print(f"[{agent_id}] This script is for MODERATOR only")
        return

    print(f"[{agent_id}] 🚀 ReAct Moderator starting...")

    # メッセージブローカーの初期化
    message_broker.initialize_db()
    print(f"[{agent_id}] 📬 Message broker initialized")

    # モデレーターの初期化
    moderator = SimpleReActModerator(agent_id)

    print(f"[{agent_id}] 🤖 ReAct Moderator ready. Waiting for START_DEBATE message...")

    # メインループ
    while moderator.debate_state["current_phase"] != "COMPLETE":
        try:
            # ReActサイクルの実行
            result = moderator.think_and_act()

            if result:
                print(
                    f"[{agent_id}] 📊 Action result: {result.get('type', 'unknown')}")

            # 短い間隔でポーリング
            time.sleep(2)

        except KeyboardInterrupt:
            print(f"\n[{agent_id}] 🛑 Moderator interrupted by user")
            break
        except Exception as e:
            print(f"[{agent_id}] ❌ Error in main loop: {e}")
            time.sleep(5)  # エラー時は少し長めに待機

    print(f"[{agent_id}] 🏁 ReAct Moderator shutting down")


if __name__ == "__main__":
    main_loop()
