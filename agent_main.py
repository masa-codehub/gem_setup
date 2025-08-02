#!/usr/bin/env python3
"""
統合エージェントメイン
クリーンアーキテクチャ（Clean Architecture）と従来システムの統合版
"""

import os
import subprocess
import json
import time
import sqlite3
from typing import Optional

# クリーンアーキテクチャのインポート（利用可能な場合）
try:
    from main.application.use_cases import (
        SubmitStatementUseCase,
        SubmitRebuttalUseCase,
        SubmitJudgementUseCase
    )
    from main.application.interfaces import (
        IMessageBroker, IDebateHistoryService, IErrorNotificationService
    )
    from main.infrastructure.message_broker import SqliteMessageBroker
    from main.infrastructure.gemini_service import GeminiService
    from main.infrastructure.file_repository import FileBasedPromptRepository
    from main.domain.models import Message
    CLEAN_ARCHITECTURE_AVAILABLE = True
    print("[SYSTEM] Clean Architecture modules loaded successfully")
except ImportError as e:
    CLEAN_ARCHITECTURE_AVAILABLE = False
    print(f"[SYSTEM] Clean Architecture not available: {e}")
    print("[SYSTEM] Falling back to legacy implementation")

AGENT_ID = os.environ.get("AGENT_ID")
DEBATE_DIR = os.environ.get("DEBATE_DIR")
CONFIG_DIR = "./config"
BROKER_CMD = ["python3", "message_broker.py"]


# クリーンアーキテクチャサービスの実装（利用可能な場合）
if CLEAN_ARCHITECTURE_AVAILABLE:
    class DebateHistoryService(IDebateHistoryService):
        """討論履歴管理サービス"""

        def __init__(self, message_broker: IMessageBroker):
            self.message_broker = message_broker
            self.debate_dir = os.environ.get("DEBATE_DIR", ".")

        def get_debate_history(self) -> list:
            """これまでの討論履歴を取得する"""
            try:
                db_file = os.path.join(self.debate_dir, "messages.db")

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
                                'content': msg.get('payload', {}).get(
                                    'content', ''
                                )
                            })
                    return history
            except Exception:
                return []

    class ErrorNotificationService(IErrorNotificationService):
        """エラー通知サービス"""

        def __init__(self, message_broker: IMessageBroker):
            self.message_broker = message_broker

        def notify_system_error(self, error_message: str,
                                agent_id: str) -> None:
            """システムエラーを通知する"""
            timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            error_msg = Message(
                turn_id=-1,
                timestamp=timestamp,
                sender_id=agent_id,
                recipient_id="MODERATOR",
                message_type="SYSTEM_ERROR",
                payload={
                    "content": error_message,
                    "error_agent": agent_id
                }
            )

            try:
                self.message_broker.post_message(error_msg)
            except Exception:
                pass  # エラー通知の失敗は無視

    class AgentOrchestrator:
        """クリーンアーキテクチャベースのエージェントオーケストレーター"""

        def __init__(self, agent_id: str):
            self.agent_id = agent_id

            # インフラストラクチャ層の初期化
            self.message_broker = SqliteMessageBroker()
            self.llm_service = GeminiService()
            self.prompt_repository = FileBasedPromptRepository()
            self.history_service = DebateHistoryService(self.message_broker)
            self.error_service = ErrorNotificationService(self.message_broker)

            # ユースケースの初期化（依存性注入）
            self.statement_use_case = SubmitStatementUseCase(
                llm_service=self.llm_service,
                message_broker=self.message_broker,
                prompt_repository=self.prompt_repository
            )

            self.rebuttal_use_case = SubmitRebuttalUseCase(
                llm_service=self.llm_service,
                message_broker=self.message_broker,
                prompt_repository=self.prompt_repository,
                history_service=self.history_service
            )

            self.judgement_use_case = SubmitJudgementUseCase(
                llm_service=self.llm_service,
                message_broker=self.message_broker,
                prompt_repository=self.prompt_repository,
                history_service=self.history_service
            )

            # データベース初期化
            self.message_broker.initialize_db()

        def handle_message(self, message: Message) -> Optional[str]:
            """メッセージ処理の統合ロジック"""
            message_type = message.message_type
            turn_id = message.turn_id
            topic = "人工知能の発達は人類にとって有益か有害か"

            try:
                if message_type == "PROMPT_FOR_STATEMENT":
                    self.statement_use_case.execute(
                        topic, self.agent_id, turn_id
                    )
                    return None

                elif message_type == "PROMPT_FOR_REBUTTAL":
                    self.rebuttal_use_case.execute(
                        topic, self.agent_id, turn_id
                    )
                    return None

                elif message_type == "PROMPT_FOR_CLOSING_STATEMENT":
                    # 最終弁論も反駁ユースケースを流用（履歴を使う）
                    self.rebuttal_use_case.execute(
                        topic, self.agent_id, turn_id
                    )
                    return None

                elif message_type == "REQUEST_JUDGEMENT":
                    if self.agent_id.startswith("JUDGE_"):
                        self.judgement_use_case.execute(
                            topic, self.agent_id, turn_id
                        )
                    return None

                elif message_type == "END_DEBATE":
                    return "EXIT"

                # その他のメッセージは無視
                return None

            except RuntimeError as e:
                self.error_service.notify_system_error(str(e), self.agent_id)
                return None

        def run_clean_architecture(self):
            """クリーンアーキテクチャベースのメインループ"""
            print(f"[{self.agent_id}] Clean Architecture Agent started")

            while True:
                try:
                    # 新しいメッセージをチェック
                    message = self.message_broker.get_message(self.agent_id)

                    if message:
                        print(f"[{self.agent_id}] Processing: "
                              f"{message.message_type}")

                        result = self.handle_message(message)

                        if result == "EXIT":
                            break

                        if result:
                            print(f"[{self.agent_id}] Result: {result}")

                    # ポーリング間隔
                    time.sleep(3)

                except KeyboardInterrupt:
                    print(f"\n[{self.agent_id}] Agent interrupted by user")
                    break
                except Exception as e:
                    print(f"[{self.agent_id}] Error in main loop: {e}")
                    self.error_service.notify_system_error(
                        str(e), self.agent_id
                    )
                    time.sleep(5)

            print(f"[{self.agent_id}] Agent shutting down")


# 従来システムの関数群（既存互換性のため保持）


def get_my_message():
    """自分宛のメッセージをブローカーから取得する"""
    try:
        result = subprocess.run(
            BROKER_CMD + ["get", AGENT_ID],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            try:
                message = json.loads(result.stdout.strip())
                msg_type = message.get('message_type', 'UNKNOWN')
                print(f"[{AGENT_ID}] 📨 Received: {msg_type}")
                return message
            except json.JSONDecodeError as e:
                print(f"[{AGENT_ID}] 📄 JSON decode error: {e}")
                print(f"[{AGENT_ID}] 📄 Raw output: '{result.stdout}'")
        elif result.stderr:
            print(f"[{AGENT_ID}] ⚠️  Retrieval error: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print(f"[{AGENT_ID}] ⏰ Message retrieval timeout")
    except json.JSONDecodeError as e:
        print(f"[{AGENT_ID}] 📄 JSON decode error: {e}")
    except Exception as e:
        print(f"[{AGENT_ID}] ❌ Unexpected error getting message: {e}")
    return None


def post_message_to_recipient(recipient_id, message_body):
    """指定した相手にメッセージを投稿する"""
    try:
        result = subprocess.run(
            BROKER_CMD + ["post", recipient_id, json.dumps(message_body)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            msg_type = message_body.get('message_type', 'UNKNOWN')
            print(f"[{AGENT_ID}] 📤 Sent message to {recipient_id}: {msg_type}")
        else:
            print(f"[{AGENT_ID}] ❌ Failed to send message: {result.stderr}")
    except subprocess.TimeoutExpired:
        print(f"[{AGENT_ID}] ⏰ Message sending timeout")
    except Exception as e:
        print(f"[{AGENT_ID}] ❌ Unexpected error sending message: {e}")


def call_gemini(prompt: str, system_prompt: str = "") -> str:
    """Gemini APIを呼び出して応答を取得する"""
    print(f"[{AGENT_ID}] Calling Gemini API...")
    try:
        # Geminiコマンドを構築
        cmd = ["gemini"]

        if system_prompt:
            cmd.extend(["-s", system_prompt])

        cmd.extend(["-p", prompt])

        # より長いタイムアウトでGemini APIを呼び出し
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            response = result.stdout.strip()
            print(f"[{AGENT_ID}] Gemini response received "
                  f"({len(response)} chars)")
            return response
        else:
            error_msg = result.stderr.strip()
            print(f"[{AGENT_ID}] Gemini error: {error_msg}")
            # Geminiエラーの場合はシステムエラーを発生させる
            raise RuntimeError(f"Gemini API error: {error_msg}")

    except subprocess.TimeoutExpired:
        print(f"[{AGENT_ID}] Gemini timeout - system error")
        raise RuntimeError("Gemini API timeout")
    except FileNotFoundError:
        print(f"[{AGENT_ID}] Gemini command not found")
        raise RuntimeError("Gemini command not available")


def send_system_error_to_moderator(error_message: str):
    """システムエラーをモデレータに通知"""
    timestamp = subprocess.run(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ'],
                               capture_output=True, text=True).stdout.strip()
    error_msg = {
        "turn_id": -1,
        "timestamp": timestamp,
        "sender_id": AGENT_ID,
        "recipient_id": "MODERATOR",
        "message_type": "SYSTEM_ERROR",
        "payload": {
            "content": error_message,
            "error_agent": AGENT_ID
        }
    }

    try:
        post_message_to_recipient("MODERATOR", error_msg)
        print(f"[{AGENT_ID}] System error sent to MODERATOR: {error_message}")
    except Exception as e:
        print(f"[{AGENT_ID}] Failed to send error to MODERATOR: {e}")


def think(context: dict) -> dict:
    """geminiを呼び出して、応答を生成する"""
    message_type = context.get("message_type")
    turn_id = context.get("turn_id", 0)

    print(f"[{AGENT_ID}] Thinking about: {message_type}")

    # モデレーターは従来の状態遷移ロジックを使用
    if AGENT_ID == "MODERATOR":
        return handle_moderator_logic(context, turn_id)

    # 他のエージェントはGemini APIを使用
    else:
        return call_gemini_for_agent(context, turn_id)


def get_debate_history():
    """これまでの討論履歴を取得する"""
    try:
        db_file = os.path.join(DEBATE_DIR, "messages.db")
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
                if msg.get('message_type') in ['SUBMIT_STATEMENT',
                                               'SUBMIT_CROSS_EXAMINATION',
                                               'SUBMIT_REBUTTAL',
                                               'SUBMIT_CLOSING_STATEMENT']:
                    history.append({
                        'type': msg.get('message_type'),
                        'sender': msg.get('sender_id'),
                        'content': msg.get('payload', {}).get('content', '')
                    })
            return history
    except Exception as e:
        print(f"[{AGENT_ID}] Error getting debate history: {e}")
        return []


def call_gemini_for_agent(context: dict, turn_id: int) -> dict:
    """エージェント用のGemini呼び出しとレスポンス生成"""
    print(f"[{AGENT_ID}] Starting call_gemini_for_agent")

    # ペルソナファイルを読み込み
    persona_file = os.path.join(CONFIG_DIR, f"{AGENT_ID.lower()}.md")
    persona_content = ""
    try:
        with open(persona_file, 'r', encoding='utf-8') as f:
            persona_content = f.read()
        print(f"[{AGENT_ID}] Loaded persona file: "
              f"{len(persona_content)} chars")
    except FileNotFoundError:
        print(f"[{AGENT_ID}] Persona file not found: {persona_file}")
    except Exception as e:
        print(f"[{AGENT_ID}] Error loading persona: {e}")

    # プロンプト作成
    if AGENT_ID in ["DEBATER_A", "DEBATER_N"]:
        print(f"[{AGENT_ID}] Calling handle_debater_with_gemini")
        return handle_debater_with_gemini(context, turn_id, persona_content)
    elif AGENT_ID in ["JUDGE_L", "JUDGE_E", "JUDGE_R"]:
        print(f"[{AGENT_ID}] Calling handle_judge_with_gemini")
        return handle_judge_with_gemini(context, turn_id, persona_content)
    elif AGENT_ID == "ANALYST":
        print(f"[{AGENT_ID}] Calling handle_analyst_with_gemini")
        return handle_analyst_with_gemini(context, turn_id, persona_content)

    print(f"[{AGENT_ID}] No handler found, returning None")
    return None


def handle_debater_with_gemini(context: dict, turn_id: int,
                               persona: str) -> dict:
    """討論者のGemini呼び出し処理"""
    print(f"[{AGENT_ID}] Starting handle_debater_with_gemini")

    message_type = context.get("message_type")
    print(f"[{AGENT_ID}] Message type: {message_type}")

    base_response = {
        "turn_id": turn_id + 1,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sender_id": AGENT_ID,
        "recipient_id": "MODERATOR"
    }

    # 討論トピック（固定で設定、後で動的にも可能）
    topic = "人工知能の発達は人類にとって有益か有害か"

    if message_type == "PROMPT_FOR_STATEMENT":
        print(f"[{AGENT_ID}] Generating opening statement")
        prompt = f"""あなたは{AGENT_ID}として討論に参加します。

{persona}

討論トピック：{topic}

あなたの立場：
- DEBATER_A: 人工知能の発達は人類にとって有益である
- DEBATER_N: 人工知能の発達は人類にとって有害である

あなたの開始声明を300文字程度で述べてください。論理的で説得力のある議論を展開してください。"""

        print(f"[{AGENT_ID}] Calling call_gemini with prompt length: "
              f"{len(prompt)}")
        try:
            response_text = call_gemini(prompt)
            print(f"[{AGENT_ID}] Got response: {len(response_text)} chars")
        except RuntimeError as e:
            error_msg = f"Gemini API error in {AGENT_ID}: {str(e)}"
            send_system_error_to_moderator(error_msg)
            print(f"[{AGENT_ID}] Sent system error, exiting agent")
            exit(1)

        return {
            **base_response,
            "message_type": "SUBMIT_STATEMENT",
            "payload": {"content": response_text}
        }

    elif message_type == "PROMPT_FOR_CROSS_EXAMINATION":
        print(f"[{AGENT_ID}] Generating cross-examination")
        # 討論履歴を取得
        history = get_debate_history()
        history_text = ""
        for h in history:
            history_text += f"{h['sender']}: {h['content']}\n\n"

        prompt = f"""あなたは{AGENT_ID}として反対尋問を行います。

{persona}

討論トピック：{topic}

これまでの議論：
{history_text}

相手の立論に対して効果的な質問や追及を200文字程度で行ってください。
相手の論点の弱点を探り、議論の矛盾や根拠の不足を指摘してください。"""

        try:
            response_text = call_gemini(prompt)
            print(f"[{AGENT_ID}] Got cross-examination: "
                  f"{len(response_text)} chars")
        except RuntimeError as e:
            error_msg = f"Gemini API error in {AGENT_ID}: {str(e)}"
            send_system_error_to_moderator(error_msg)
            print(f"[{AGENT_ID}] Sent system error, exiting agent")
            exit(1)

        return {
            **base_response,
            "message_type": "SUBMIT_CROSS_EXAMINATION",
            "payload": {"content": response_text}
        }

    elif message_type == "PROMPT_FOR_REBUTTAL":
        # 討論履歴を取得
        history = get_debate_history()
        history_text = ""
        for h in history:
            history_text += f"{h['sender']}: {h['content']}\n\n"

        prompt = f"""あなたは{AGENT_ID}として討論を続けます。

{persona}

討論トピック：{topic}

これまでの議論：
{history_text}

上記の相手の主張を踏まえ、あなたの反駁を300文字程度で述べてください。
相手の論点に対する具体的な反論を含めてください。"""

        try:
            response_text = call_gemini(prompt)
        except RuntimeError as e:
            error_msg = f"Gemini API error in {AGENT_ID}: {str(e)}"
            send_system_error_to_moderator(error_msg)
            print(f"[{AGENT_ID}] Sent system error, exiting agent")
            exit(1)

        return {
            **base_response,
            "message_type": "SUBMIT_REBUTTAL",
            "payload": {"content": response_text}
        }

    elif message_type == "PROMPT_FOR_CLOSING_STATEMENT":
        # 討論履歴を取得
        history = get_debate_history()
        history_text = ""
        for h in history:
            history_text += f"{h['sender']}: {h['content']}\n\n"

        prompt = f"""あなたは{AGENT_ID}として討論の最終声明を行います。

{persona}

討論トピック：{topic}

これまでの議論：
{history_text}

上記の議論を総括し、あなたの立場を強化する最終声明を300文字程度で述べてください。
説得力のある結論で締めくくってください。"""

        try:
            response_text = call_gemini(prompt)
        except RuntimeError as e:
            error_msg = f"Gemini API error in {AGENT_ID}: {str(e)}"
            send_system_error_to_moderator(error_msg)
            print(f"[{AGENT_ID}] Sent system error, exiting agent")
            exit(1)

        return {
            **base_response,
            "message_type": "SUBMIT_CLOSING_STATEMENT",
            "payload": {"content": response_text}
        }

    # レビューメッセージには応答しない
    return None


def handle_judge_with_gemini(context: dict, turn_id: int,
                             persona: str) -> dict:
    """ジャッジのGemini呼び出し処理"""
    message_type = context.get("message_type")

    base_response = {
        "turn_id": turn_id + 1,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sender_id": AGENT_ID,
        "recipient_id": "MODERATOR"
    }

    if message_type == "REQUEST_JUDGEMENT":
        # 討論履歴を取得
        history = get_debate_history()
        history_text = ""
        for h in history:
            history_text += f"{h['sender']}: {h['content']}\n\n"

        prompt = f"""あなたは{AGENT_ID}として討論の判定を行います。

{persona}

討論トピック：人工知能の発達は人類にとって有益か有害か

完全な討論内容：
{history_text}

DEBATER_A（有益派）とDEBATER_N（有害派）の討論を以下の観点で評価してください：

## 評価項目（各10点満点）

### 1. 論理性と一貫性
- 主張の論理構造の明確さ
- 前提から結論への推論の妥当性

### 2. 証拠と根拠の充実度
- 具体的事例や数値の提示
- 主張を裏付ける根拠の十分性

### 3. 反駁の効果性
- 相手論点の正確な理解
- 効果的な反駁の展開

### 4. 最終弁論の説得力
- 自身立場の強化
- 聞き手への印象力

### 5. 総合評価
- 全体的な議論の質

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
            error_msg = f"Gemini API error in {AGENT_ID}: {str(e)}"
            send_system_error_to_moderator(error_msg)
            print(f"[{AGENT_ID}] Sent system error, exiting agent")
            exit(1)

        # スコアを抽出（新しいフォーマットに対応）
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

    # レビューメッセージには応答しない
    return None


def handle_analyst_with_gemini(context: dict, turn_id: int,
                               persona: str) -> dict:
    """アナリストのGemini呼び出し処理"""
    message_type = context.get("message_type")

    # ディベート結果を受信した場合、レポートを生成
    if message_type == "DEBATE_RESULTS":
        print(f"[{AGENT_ID}] Generating debate analysis report")

        # 討論履歴を取得
        history = get_debate_history()

        # 討論内容を整理
        statements = []
        cross_examinations = []
        rebuttals = []
        closing_statements = []
        judgements = []

        for h in history:
            if h['type'] == 'SUBMIT_STATEMENT':
                statements.append(f"{h['sender']}: {h['content']}")
            elif h['type'] == 'SUBMIT_CROSS_EXAMINATION':
                cross_examinations.append(f"{h['sender']}: {h['content']}")
            elif h['type'] == 'SUBMIT_REBUTTAL':
                rebuttals.append(f"{h['sender']}: {h['content']}")
            elif h['type'] == 'SUBMIT_CLOSING_STATEMENT':
                closing_statements.append(f"{h['sender']}: {h['content']}")
            elif h['type'] == 'SUBMIT_JUDGEMENT':
                judgements.append(f"{h['sender']}: {h['content']}")

        # 判定データを抽出
        judge_scores = {}
        judge_comments = {}
        for h in history:
            if h['type'] == 'SUBMIT_JUDGEMENT':
                # スコアを抽出（正規表現で）
                import re
                judge_id = h['sender']
                content = h['content']

                a_score_match = re.search(r'DEBATER_A.*?(\d+)', content)
                n_score_match = re.search(r'DEBATER_N.*?(\d+)', content)

                judge_scores[judge_id] = {
                    'debater_a': int(a_score_match.group(1))
                    if a_score_match else 0,
                    'debater_n': int(n_score_match.group(1))
                    if n_score_match else 0
                }
                judge_comments[judge_id] = content

        # レポート生成プロンプト
        prompt = f"""あなたは{AGENT_ID}として、以下のディベートの内容を
実際の討論の様子をそのまま台本形式で再現してレポートを作成してください。

{persona}

討論トピック：人工知能の発達は人類にとって有益か有害か

=== 1. 立論 ===
{chr(10).join(statements)}

=== 2. 反対尋問 ===
{chr(10).join(cross_examinations)}

=== 3. 反駁 ===
{chr(10).join(rebuttals)}

=== 4. 最終弁論 ===
{chr(10).join(closing_statements)}

=== 5. 判定結果 ===
{chr(10).join(judgements)}

以下の台本形式で、実際のディベートの進行をそのまま再現してください：

## ディベート台本

**MODERATOR**: それでは、「人工知能の発達は人類にとって有益か有害か」について
討論を開始します。まず肯定側のDEBATER_Aさん、立論をお願いします。

**DEBATER_A**: [実際の立論内容をここに記述]

**MODERATOR**: ありがとうございます。続いて否定側のDEBATER_Nさん、立論をお願いします。

**DEBATER_N**: [実際の立論内容をここに記述]

**MODERATOR**: 両者の立論が終わりました。次は反対尋問に移ります。DEBATER_Aさんから、DEBATER_Nさんへ質問をお願いします。

**DEBATER_A**: [実際の反対尋問内容をここに記述]

**MODERATOR**: ありがとうございます。次はDEBATER_Nさんから、DEBATER_Aさんへ質問をお願いします。

**DEBATER_N**: [実際の反対尋問内容をここに記述]

[このように全ステップを台本形式で再現]

上記の形式で、実際のディベートの流れを忠実に台本として再現し、
1500文字程度で作成してください。"""

        try:
            response_text = call_gemini(prompt)
            print(
                f"[{AGENT_ID}] Generated analysis report: "
                f"{len(response_text)} chars")

            # レポートをファイルに保存
            report_file = os.path.join(DEBATE_DIR, "debate_analysis_report.md")
            try:
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write("# ディベート分析レポート\n\n")
                    f.write(
                        f"**生成日時**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("**トピック**: 人工知能の発達は人類にとって有益か有害か\n\n")
                    f.write(response_text)
                print(f"[{AGENT_ID}] Report saved to: {report_file}")
            except Exception as e:
                print(f"[{AGENT_ID}] Failed to save report: {e}")

            return {
                "turn_id": turn_id + 1,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                           time.gmtime()),
                "sender_id": AGENT_ID,
                "recipient_id": "MODERATOR",
                "message_type": "ANALYSIS_REPORT_COMPLETE",
                "payload": {
                    "content": "Analysis report generated successfully",
                    "report_file": report_file
                }
            }

        except RuntimeError as e:
            error_msg = f"Gemini API error in {AGENT_ID}: {str(e)}"
            send_system_error_to_moderator(error_msg)
            print(f"[{AGENT_ID}] Sent system error, exiting agent")
            exit(1)

    # その他のメッセージは観察のみ
    return None


def handle_moderator_logic(context: dict, turn_id: int) -> dict:
    """モデレーターの状態遷移ロジック"""
    message_type = context.get("message_type")
    sender_id = context.get("sender_id")

    # システムエラーの場合は緊急終了メッセージを送信
    if message_type == "SYSTEM_ERROR":
        error_agent = context.get("payload", {}).get("error_agent", "UNKNOWN")
        error_content = context.get("payload", {}).get("content", "")
        print(f"[{AGENT_ID}] SYSTEM ERROR from {error_agent}: {error_content}")
        print(f"[{AGENT_ID}] Terminating debate due to system error")

        # システムエラーのため、プロセス終了
        print(f"[{AGENT_ID}] Exiting due to system error")
        exit(1)

    base_response = {
        "turn_id": turn_id + 1,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sender_id": AGENT_ID
    }

    # Store a separate message for the next prompt
    def send_next_prompt(base_resp, next_recipient, next_msg_type, content):
        return {
            **base_resp,
            "recipient_id": next_recipient,
            "message_type": next_msg_type,
            "payload": {"content": content}
        }

    if message_type == "START_DEBATE":
        return {
            **base_response,
            "recipient_id": "DEBATER_A",
            "message_type": "PROMPT_FOR_STATEMENT",
            "payload": {"content": "Please provide your opening statement."}
        }

    elif message_type == "SUBMIT_STATEMENT" and sender_id == "DEBATER_A":
        # We need to handle both: send review and prompt next debater
        # For now, we'll handle the review first
        return {
            **base_response,
            "recipient_id": ["DEBATER_N", "JUDGE_L", "JUDGE_E", "JUDGE_R"],
            "message_type": "STATEMENT_FOR_REVIEW",
            "payload": context.get("payload", {}),
            "next_action": {
                "recipient_id": "DEBATER_N",
                "message_type": "PROMPT_FOR_STATEMENT",
                "payload": {
                    "content": "Please provide your opening statement."
                }
            }
        }

    elif message_type == "SUBMIT_STATEMENT" and sender_id == "DEBATER_N":
        return {
            **base_response,
            "recipient_id": ["DEBATER_A", "JUDGE_L", "JUDGE_E", "JUDGE_R"],
            "message_type": "STATEMENT_FOR_REVIEW",
            "payload": context.get("payload", {}),
            "next_action": {
                "recipient_id": "DEBATER_A",
                "message_type": "PROMPT_FOR_CROSS_EXAMINATION",
                "payload": {
                    "content": ("Please provide your cross-examination "
                                "questions.")
                }
            }
        }

    elif (message_type == "SUBMIT_CROSS_EXAMINATION" and
          sender_id == "DEBATER_A"):
        return {
            **base_response,
            "recipient_id": ["DEBATER_N", "JUDGE_L", "JUDGE_E", "JUDGE_R"],
            "message_type": "CROSS_EXAMINATION_FOR_REVIEW",
            "payload": context.get("payload", {}),
            "next_action": {
                "recipient_id": "DEBATER_N",
                "message_type": "PROMPT_FOR_CROSS_EXAMINATION",
                "payload": {
                    "content": ("Please provide your cross-examination "
                                "questions.")
                }
            }
        }

    elif (message_type == "SUBMIT_CROSS_EXAMINATION" and
          sender_id == "DEBATER_N"):
        return {
            **base_response,
            "recipient_id": ["DEBATER_A", "JUDGE_L", "JUDGE_E", "JUDGE_R"],
            "message_type": "CROSS_EXAMINATION_FOR_REVIEW",
            "payload": context.get("payload", {}),
            "next_action": {
                "recipient_id": "DEBATER_A",
                "message_type": "PROMPT_FOR_REBUTTAL",
                "payload": {"content": "Please provide your rebuttal."}
            }
        }

    elif message_type == "SUBMIT_REBUTTAL" and sender_id == "DEBATER_A":
        return {
            **base_response,
            "recipient_id": ["DEBATER_N", "JUDGE_L", "JUDGE_E", "JUDGE_R"],
            "message_type": "REBUTTAL_FOR_REVIEW",
            "payload": context.get("payload", {}),
            "next_action": {
                "recipient_id": "DEBATER_N",
                "message_type": "PROMPT_FOR_REBUTTAL",
                "payload": {"content": "Please provide your rebuttal."}
            }
        }

    elif message_type == "SUBMIT_REBUTTAL" and sender_id == "DEBATER_N":
        return {
            **base_response,
            "recipient_id": ["DEBATER_A", "JUDGE_L", "JUDGE_E", "JUDGE_R"],
            "message_type": "REBUTTAL_FOR_REVIEW",
            "payload": context.get("payload", {}),
            "next_action": {
                "recipient_id": "DEBATER_A",
                "message_type": "PROMPT_FOR_CLOSING_STATEMENT",
                "payload": {
                    "content": "Please provide your closing statement."
                }
            }
        }

    elif (message_type == "SUBMIT_CLOSING_STATEMENT" and
          sender_id == "DEBATER_A"):
        return {
            **base_response,
            "recipient_id": ["DEBATER_N", "JUDGE_L", "JUDGE_E", "JUDGE_R"],
            "message_type": "CLOSING_STATEMENT_FOR_REVIEW",
            "payload": context.get("payload", {}),
            "next_action": {
                "recipient_id": "DEBATER_N",
                "message_type": "PROMPT_FOR_CLOSING_STATEMENT",
                "payload": {
                    "content": "Please provide your closing statement."
                }
            }
        }

    elif (message_type == "SUBMIT_CLOSING_STATEMENT" and
          sender_id == "DEBATER_N"):
        return {
            **base_response,
            "recipient_id": ["DEBATER_A", "JUDGE_L", "JUDGE_E", "JUDGE_R"],
            "message_type": "CLOSING_STATEMENT_FOR_REVIEW",
            "payload": context.get("payload", {}),
            "next_action": {
                "recipient_id": ["JUDGE_L", "JUDGE_E", "JUDGE_R"],
                "message_type": "REQUEST_JUDGEMENT",
                "payload": {"content": "Please provide your final judgement."}
            }
        }

    elif message_type == "SUBMIT_JUDGEMENT":
        # Handle judgement collection (simplified for now)
        return {
            **base_response,
            "recipient_id": ["DEBATER_A", "DEBATER_N", "JUDGE_L",
                             "JUDGE_E", "JUDGE_R", "ANALYST"],
            "message_type": "DEBATE_RESULTS",
            "payload": {"content": "Debate concluded. Results available."}
        }

    elif message_type == "ANALYSIS_REPORT_COMPLETE":
        print(f"[{AGENT_ID}] Analysis report completed by ANALYST")
        print(f"[{AGENT_ID}] Debate session concluded with full analysis")
        return None

    return None


def handle_debater_logic(context: dict, turn_id: int) -> dict:
    """討論者のロジック"""
    message_type = context.get("message_type")

    base_response = {
        "turn_id": turn_id + 1,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sender_id": AGENT_ID,
        "recipient_id": "MODERATOR"
    }

    if message_type == "PROMPT_FOR_STATEMENT":
        return {
            **base_response,
            "message_type": "SUBMIT_STATEMENT",
            "payload": {
                "content": (f"This is {AGENT_ID}'s opening statement "
                            f"on the topic.")
            }
        }

    elif message_type == "PROMPT_FOR_REBUTTAL":
        return {
            **base_response,
            "message_type": "SUBMIT_REBUTTAL",
            "payload": {
                "content": f"This is {AGENT_ID}'s rebuttal to the opponent."
            }
        }

    elif message_type == "PROMPT_FOR_CLOSING_STATEMENT":
        return {
            **base_response,
            "message_type": "SUBMIT_CLOSING_STATEMENT",
            "payload": {
                "content": f"This is {AGENT_ID}'s closing statement."
            }
        }

    # For review messages, debaters typically don't respond immediately
    return None


def handle_judge_logic(context: dict, turn_id: int) -> dict:
    """ジャッジのロジック"""
    message_type = context.get("message_type")

    base_response = {
        "turn_id": turn_id + 1,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sender_id": AGENT_ID,
        "recipient_id": "MODERATOR"
    }

    if message_type == "REQUEST_JUDGEMENT":
        return {
            **base_response,
            "message_type": "SUBMIT_JUDGEMENT",
            "payload": {
                "scores": {"debater_a": 7, "debater_n": 8},
                "reasoning": f"Judgement from {AGENT_ID}"
            }
        }

    # For review messages, judges typically don't respond
    if message_type in ["STATEMENT_FOR_REVIEW", "REBUTTAL_FOR_REVIEW",
                        "CLOSING_STATEMENT_FOR_REVIEW"]:
        return None

    return None


def handle_analyst_logic(context: dict, turn_id: int) -> dict:
    """アナリストのロジック"""
    # アナリストは通常、観察のみで応答しない
    return None


def main_loop():
    """エージェントのメインループ"""
    print(f"[{AGENT_ID}] Agent started. Waiting for messages.")
    while True:
        message = get_my_message()
        if message:
            print(f"[{AGENT_ID}] Received message: "
                  f"{message.get('message_type')}")

            # 思考して応答を生成
            response = think(message)

            if response:
                recipient = response.get("recipient_id")
                # ブロードキャスト（配列）の場合は個別送信に分解
                if isinstance(recipient, list):
                    for r in recipient:
                        individual_response = response.copy()
                        individual_response["recipient_id"] = r
                        if "next_action" in individual_response:
                            del individual_response["next_action"]
                        post_message_to_recipient(r, individual_response)
                else:
                    clean_response = response.copy()
                    if "next_action" in clean_response:
                        del clean_response["next_action"]
                    post_message_to_recipient(recipient, clean_response)

                print(f"[{AGENT_ID}] Sent response: "
                      f"{response.get('message_type')}")

                # Handle next_action if present
                next_action = response.get("next_action")
                if next_action:
                    time.sleep(1)  # Brief pause before next action
                    next_recipient = next_action.get("recipient_id")
                    if isinstance(next_recipient, list):
                        for r in next_recipient:
                            individual_next = next_action.copy()
                            individual_next["recipient_id"] = r
                            individual_next["turn_id"] = response.get(
                                "turn_id", 0) + 1
                            individual_next["timestamp"] = time.strftime(
                                "%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                            individual_next["sender_id"] = AGENT_ID
                            post_message_to_recipient(r, individual_next)
                    else:
                        next_action["turn_id"] = response.get("turn_id", 0) + 1
                        next_action["timestamp"] = time.strftime(
                            "%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        next_action["sender_id"] = AGENT_ID
                        post_message_to_recipient(next_recipient, next_action)

                    print(f"[{AGENT_ID}] Sent next action: "
                          f"{next_action.get('message_type')}")

        # ポーリング間隔
        time.sleep(5)


def main():
    """統合メイン関数 - クリーンアーキテクチャと従来システムの統合"""
    print(f"[{AGENT_ID}] Starting Integrated Agent System")

    # エージェントID検証
    if not AGENT_ID:
        print("[ERROR] AGENT_ID environment variable not set")
        return

    # 環境変数によるアーキテクチャ選択
    use_clean_architecture = (
        os.environ.get("USE_CLEAN_ARCHITECTURE", "true").lower() == "true"
    )

    if CLEAN_ARCHITECTURE_AVAILABLE and use_clean_architecture:
        print(f"[{AGENT_ID}] Using Clean Architecture implementation")

        # モデレーター以外はクリーンアーキテクチャを使用
        if AGENT_ID != "MODERATOR":
            valid_agents = [
                "DEBATER_A", "DEBATER_N", "JUDGE_L",
                "JUDGE_E", "JUDGE_R", "ANALYST"
            ]
            if AGENT_ID not in valid_agents:
                print(f"[{AGENT_ID}] Invalid agent ID. "
                      f"Must be one of: {valid_agents}")
                return

            # クリーンアーキテクチャオーケストレーターを実行
            orchestrator = AgentOrchestrator(AGENT_ID)
            orchestrator.run_clean_architecture()
        else:
            # モデレーターは従来システムを使用
            print(f"[{AGENT_ID}] MODERATOR using legacy system")
            main_loop()
    else:
        print(f"[{AGENT_ID}] Using legacy implementation")
        main_loop()


if __name__ == "__main__":
    main()
