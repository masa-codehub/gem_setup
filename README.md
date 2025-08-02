# AI Debate System with Message Broker

## 概要

このプロジェクトは、メッセージブローカーを使用した分散型AIディベートシステムです。複数のAIエージェントが非同期でメッセージをやり取りしながら、構造化されたディベートを行います。

## 主要コンポーネント

### 1. 統一マスタースクリプト
- **`run_debate.sh`**: メッセージブローカーベースの統一ディベートオーケストレーター

### 2. メッセージブローカー
- **`message_broker.py`**: SQLiteベースの非同期メッセージングシステム

### 3. エージェントシステム
- **`agent_main.py`**: 各AIエージェントのメインプロセス

### 4. テストとユーティリティ
- **`test_message_broker.py`**: システム統合テストスクリプト

## クイックスタート

### 基本実行
```bash
./run_debate.sh
```

### カスタムタイムアウト設定
```bash
TIMEOUT_DURATION=1200 ./run_debate.sh  # 20分
```

### システムテスト
```bash
python3 test_message_broker.py
```

## エージェント構成

1. **MODERATOR**: ディベートの司会進行
2. **DEBATER_A**: 肯定側討論者
3. **DEBATER_N**: 否定側討論者  
4. **JUDGE_L**: 論理性重視の審査員
5. **JUDGE_E**: 倫理性重視の審査員
6. **JUDGE_R**: 修辞技法重視の審査員
7. **ANALYST**: 全体分析担当

## 結果の確認

### リアルタイム監視
ディベート実行中にリアルタイムで進行状況が表示されます：
- 経過時間とタイムアウトまでの残り時間
- 処理されたメッセージ数
- アクティブなエージェント数

### 詳細統計
```bash
cd debate_runs/[DEBATE_ID]
python3 ../message_broker.py stats
```

### ログファイル
各エージェントのログは `debate_runs/[DEBATE_ID]/[AGENT].log` に保存されます。

## システムアーキテクチャの改善点

### ✅ 完了した統合
- **単一エントリポイント**: `run_debate.sh` による統一実行
- **メッセージブローカー統合**: 非同期メッセージング
- **リアルタイム監視**: 進行状況の可視化
- **堅牢なエラーハンドリング**: プロセス管理とクリーンアップ
- **詳細な統計**: メッセージ分析とパフォーマンス計測

### 🔧 技術仕様
- **メッセージキュー**: SQLiteベース
- **プロセス管理**: バックグラウンド実行と自動クリーンアップ
- **ログ管理**: エージェント別ログファイル
- **統計分析**: メッセージタイプ別集計

## ファイル構造

```
/app/
├── run_debate.sh              # 🎯 統一メインスクリプト
├── message_broker.py          # 📬 メッセージブローカー
├── agent_main.py              # 🤖 エージェントメイン
├── test_message_broker.py     # 🧪 テストスクリプト
├── config/                    # ⚙️ エージェント設定
├── debate_runs/               # 📊 実行結果
└── docs/                      # 📚 ドキュメント
```

## トラブルシューティング

### エージェントが応答しない場合
```bash
# プロセス確認
ps aux | grep agent_main.py

# ログ確認  
tail -f debate_runs/[DEBATE_ID]/[AGENT].log
```

### メッセージ配信の問題
```bash
# メッセージ状況確認
DEBATE_DIR=./debate_runs/[DEBATE_ID] python3 message_broker.py stats
```

## 設定のカスタマイズ

### タイムアウト時間
```bash
export TIMEOUT_DURATION=1800  # 30分
./run_debate.sh
```

### エージェント設定
`config/` ディレクトリ内の各エージェント設定ファイルを編集してください。

## 詳細ドキュメント

- **統合ガイド**: `MESSAGE_BROKER_INTEGRATION.md`
- **最適化マニュアル**: `OPTIMIZATION_MANUAL.md`

---

**🎉 メッセージブローカー統合により、スケーラブルで堅牢なAIディベートシステムが実現されました！**
