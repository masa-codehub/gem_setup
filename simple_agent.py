#!/usr/bin/env python3
"""
シンプル化されたエージェントシステム
モデレーター以外のエージェント用
"""

import os
import time
import json
import subprocess
import message_broker


def call_gemini(prompt: str, system_prompt: str = "") -> str:
    """Gemini APIを呼び出して応答を取得する"""
    agent_id = os.environ.get("AGENT_ID", "UNKNOWN")
    print(f"[{agent_id}] Calling Gemini API...")

    try:
        cmd = ["gemini"]
        if system_prompt:
            cmd.extend(["-s", system_prompt])
        cmd.extend(["-p", prompt])

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=90
        )

        if result.returncode == 0:
            response = result.stdout.strip()
            print(f"[{agent_id}] Gemini response received ({len(response)} chars)")
            return response
        else:
            error_msg = result.stderr.strip()
            print(f"[{agent_id}] Gemini error: {error_msg}")
            raise RuntimeError(f"Gemini API error: {error_msg}")

    except subprocess.TimeoutExpired:
        print(f"[{agent_id}] Gemini timeout")
        raise RuntimeError("Gemini API timeout")
    except FileNotFoundError:
        print(f"[{agent_id}] Gemini command not found")
        raise RuntimeError("Gemini command not available")


def send_system_error_to_moderator(error_message: str):
    """システムエラーをモデレータに通知"""
    agent_id = os.environ.get("AGENT_ID", "UNKNOWN")
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    error_msg = {
        "turn_id": -1,
        "timestamp": timestamp,
        "sender_id": agent_id,
        "recipient_id": "MODERATOR",
        "message_type": "SYSTEM_ERROR",
        "payload": {
            "content": error_message,
            "error_agent": agent_id
        }
    }

    try:
        message_broker.post_message("MODERATOR", error_msg)
        print(f"[{agent_id}] System error sent to MODERATOR: {error_message}")
    except Exception as e:
        print(f"[{agent_id}] Failed to send error to MODERATOR: {e}")


def get_debate_history():
    """これまでの討論履歴を取得する"""
    agent_id = os.environ.get("AGENT_ID", "UNKNOWN")
    debate_dir = os.environ.get("DEBATE_DIR", ".")

    try:
        db_file = os.path.join(debate_dir, "messages.db")

        import sqlite3
        with sqlite3.connect(db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT message_body FROM messages
                WHERE is_read = 1
                ORDER BY created_at
            """)
            rows = cursor.fetchall()

            history = []
            for row in rows:
                msg = json.loads(row['message_body'])
                if msg.get('message_type') in [
                    'SUBMIT_STATEMENT', 'SUBMIT_REBUTTAL',
                    'SUBMIT_CLOSING_STATEMENT', 'SUBMIT_JUDGEMENT'
                ]:
                    history.append({
                        'type': msg.get('message_type'),
                        'sender': msg.get('sender_id'),
                        'content': msg.get('payload', {}).get('content', '')
                    })
            return history
    except Exception as e:
        print(f"[{agent_id}] Error getting debate history: {e}")
        return []


def handle_debater_message(message: dict, persona: str) -> dict:
    """討論者のメッセージ処理"""
    agent_id = os.environ.get("AGENT_ID", "UNKNOWN")
    message_type = message.get("message_type")
    turn_id = message.get("turn_id", 0)

    print(f"[{agent_id}] Processing: {message_type}")

    base_response = {
        "turn_id": turn_id + 1,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sender_id": agent_id,
        "recipient_id": "MODERATOR"
    }

    topic = "人工知能の発達は人類にとって有益か有害か"

    if message_type == "PROMPT_FOR_STATEMENT":
        prompt = f"""あなたは{agent_id}として討論に参加します。

{persona}

討論トピック：{topic}

あなたの立場：
- DEBATER_A: 人工知能の発達は人類にとって有益である
- DEBATER_N: 人工知能の発達は人類にとって有害である

あなたの開始声明を300文字程度で述べてください。論理的で説得力のある議論を展開してください。"""

        try:
            response_text = call_gemini(prompt)
        except RuntimeError as e:
            send_system_error_to_moderator(str(e))
            return None

        return {
            **base_response,
            "message_type": "SUBMIT_STATEMENT",
            "payload": {"content": response_text}
        }

    elif message_type == "PROMPT_FOR_REBUTTAL":
        history = get_debate_history()
        history_text = "\n\n".join(
            [f"{h['sender']}: {h['content']}" for h in history])

        prompt = f"""あなたは{agent_id}として討論を続けます。

{persona}

討論トピック：{topic}

これまでの議論：
{history_text}

上記の相手の主張を踏まえ、あなたの反駁を300文字程度で述べてください。
相手の論点に対する具体的な反論を含めてください。"""

        try:
            response_text = call_gemini(prompt)
        except RuntimeError as e:
            send_system_error_to_moderator(str(e))
            return None

        return {
            **base_response,
            "message_type": "SUBMIT_REBUTTAL",
            "payload": {"content": response_text}
        }

    elif message_type == "PROMPT_FOR_CLOSING_STATEMENT":
        history = get_debate_history()
        history_text = "\n\n".join(
            [f"{h['sender']}: {h['content']}" for h in history])

        prompt = f"""あなたは{agent_id}として討論の最終声明を行います。

{persona}

討論トピック：{topic}

これまでの議論：
{history_text}

上記の議論を総括し、あなたの立場を強化する最終声明を300文字程度で述べてください。
説得力のある結論で締めくくってください。"""

        try:
            response_text = call_gemini(prompt)
        except RuntimeError as e:
            send_system_error_to_moderator(str(e))
            return None

        return {
            **base_response,
            "message_type": "SUBMIT_CLOSING_STATEMENT",
            "payload": {"content": response_text}
        }

    elif message_type == "END_DEBATE":
        print(f"[{agent_id}] Received END_DEBATE signal. Shutting down.")
        return "EXIT"

    # レビューメッセージや他のメッセージには応答しない
    return None


def handle_judge_message(message: dict, persona: str) -> dict:
    """ジャッジのメッセージ処理"""
    agent_id = os.environ.get("AGENT_ID", "UNKNOWN")
    message_type = message.get("message_type")
    turn_id = message.get("turn_id", 0)

    base_response = {
        "turn_id": turn_id + 1,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sender_id": agent_id,
        "recipient_id": "MODERATOR"
    }

    if message_type == "REQUEST_JUDGEMENT":
        history = get_debate_history()
        history_text = "\n\n".join(
            [f"{h['sender']}: {h['content']}" for h in history])

        prompt = f"""あなたは{agent_id}として討論の判定を行います。

{persona}

討論トピック：人工知能の発達は人類にとって有益か有害か

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

        try:
            response_text = call_gemini(prompt)
        except RuntimeError as e:
            send_system_error_to_moderator(str(e))
            return None

        # スコアを抽出
        import re
        total_a_match = re.search(r'DEBATER_A.*?合計:\s*(\d+)', response_text)
        total_n_match = re.search(r'DEBATER_N.*?合計:\s*(\d+)', response_text)

        a_score = int(total_a_match.group(1)) if total_a_match else 35
        n_score = int(total_n_match.group(1)) if total_n_match else 35

        return {
            **base_response,
            "message_type": "SUBMIT_JUDGEMENT",
            "payload": {
                "scores": {"debater_a": a_score, "debater_n": n_score},
                "reasoning": response_text
            }
        }

    elif message_type == "END_DEBATE":
        print(f"[{agent_id}] Received END_DEBATE signal. Shutting down.")
        return "EXIT"

    # レビューメッセージには応答しない
    return None


def handle_analyst_message(message: dict, persona: str) -> dict:
    """アナリストのメッセージ処理"""
    agent_id = os.environ.get("AGENT_ID", "UNKNOWN")
    message_type = message.get("message_type")
    turn_id = message.get("turn_id", 0)
    debate_dir = os.environ.get("DEBATE_DIR", ".")

    if message_type == "DEBATE_RESULTS":
        print(f"[{agent_id}] Generating debate analysis report")

        history = get_debate_history()
        history_by_type = {
            'statements': [],
            'rebuttals': [],
            'closing_statements': [],
            'judgements': []
        }

        for h in history:
            if h['type'] == 'SUBMIT_STATEMENT':
                history_by_type['statements'].append(
                    f"{h['sender']}: {h['content']}")
            elif h['type'] == 'SUBMIT_REBUTTAL':
                history_by_type['rebuttals'].append(
                    f"{h['sender']}: {h['content']}")
            elif h['type'] == 'SUBMIT_CLOSING_STATEMENT':
                history_by_type['closing_statements'].append(
                    f"{h['sender']}: {h['content']}")
            elif h['type'] == 'SUBMIT_JUDGEMENT':
                history_by_type['judgements'].append(
                    f"{h['sender']}: {h['content']}")

        prompt = f"""あなたは{agent_id}として、以下のディベートの内容を分析し、
台本形式でレポートを作成してください。

{persona}

討論トピック：人工知能の発達は人類にとって有益か有害か

=== 立論 ===
{chr(10).join(history_by_type['statements'])}

=== 反駁 ===
{chr(10).join(history_by_type['rebuttals'])}

=== 最終弁論 ===
{chr(10).join(history_by_type['closing_statements'])}

=== 判定結果 ===
{chr(10).join(history_by_type['judgements'])}

以下の台本形式で、実際のディベートの進行を再現してください：

## ディベート台本

**MODERATOR**: それでは、「人工知能の発達は人類にとって有益か有害か」について討論を開始します。まず肯定側のDEBATER_Aさん、立論をお願いします。

**DEBATER_A**: [実際の立論内容]

**MODERATOR**: ありがとうございます。続いて否定側のDEBATER_Nさん、立論をお願いします。

**DEBATER_N**: [実際の立論内容]

[このように全ステップを台本形式で再現]

1500文字程度で作成してください。"""

        try:
            response_text = call_gemini(prompt)

            # レポートをファイルに保存
            report_file = os.path.join(debate_dir, "debate_analysis_report.md")
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("# ディベート分析レポート\n\n")
                f.write(f"**生成日時**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("**トピック**: 人工知能の発達は人類にとって有益か有害か\n\n")
                f.write(response_text)

            print(f"[{agent_id}] Report saved to: {report_file}")

            return {
                "turn_id": turn_id + 1,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "sender_id": agent_id,
                "recipient_id": "MODERATOR",
                "message_type": "ANALYSIS_REPORT_COMPLETE",
                "payload": {
                    "content": "Analysis report generated successfully",
                    "report_file": report_file
                }
            }

        except RuntimeError as e:
            send_system_error_to_moderator(str(e))
            return None

    elif message_type == "END_DEBATE":
        print(f"[{agent_id}] Received END_DEBATE signal. Shutting down.")
        return "EXIT"

    # その他のメッセージは観察のみ
    return None


def load_persona(agent_id: str) -> str:
    """エージェントのペルソナファイルを読み込む"""
    persona_file = f"./config/{agent_id.lower()}.md"
    try:
        with open(persona_file, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"[{agent_id}] Persona file not found: {persona_file}")
        return ""
    except Exception as e:
        print(f"[{agent_id}] Error loading persona: {e}")
        return ""


def main_loop():
    """エージェントのメインループ"""
    agent_id = os.environ.get("AGENT_ID", "UNKNOWN")

    if agent_id == "MODERATOR":
        print(f"[{agent_id}] This script is for non-moderator agents only")
        print(f"[{agent_id}] Use react_moderator.py for MODERATOR")
        return

    print(f"[{agent_id}] Simple agent started. Waiting for messages...")

    # メッセージブローカーの初期化
    message_broker.initialize_db()

    # ペルソナの読み込み
    persona = load_persona(agent_id)

    while True:
        try:
            # 新しいメッセージをチェック
            message = message_broker.get_message(agent_id)

            if message:
                print(
                    f"[{agent_id}] Received: {message.get('message_type', 'UNKNOWN')}")

                # メッセージの種類に応じて処理
                response = None

                if agent_id in ["DEBATER_A", "DEBATER_N"]:
                    response = handle_debater_message(message, persona)
                elif agent_id in ["JUDGE_L", "JUDGE_E", "JUDGE_R"]:
                    response = handle_judge_message(message, persona)
                elif agent_id == "ANALYST":
                    response = handle_analyst_message(message, persona)

                # 終了シグナルのチェック
                if response == "EXIT":
                    break

                # 応答がある場合は送信
                if response:
                    message_broker.post_message(
                        response["recipient_id"], response)
                    print(
                        f"[{agent_id}] Sent: {response.get('message_type', 'UNKNOWN')}")

            # ポーリング間隔
            time.sleep(3)

        except KeyboardInterrupt:
            print(f"\n[{agent_id}] Agent interrupted by user")
            break
        except Exception as e:
            print(f"[{agent_id}] Error in main loop: {e}")
            time.sleep(5)

    print(f"[{agent_id}] Agent shutting down")


if __name__ == "__main__":
    main_loop()
