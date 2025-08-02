#!/bin/bash

# =================================================================
#  Master Debate Orchestration Script (v4.0 - Unified Message Queue)
# =================================================================

# --- Cleanup Function ---
cleanup() {
    echo "🧹 Cleaning up background processes..."
    # Use different approaches to find and kill processes
    if command -v pkill > /dev/null 2>&1; then
        pkill -f "agent_main.py" 2>/dev/null || true
    elif command -v ps > /dev/null 2>&1; then
        # Use ps if available
        ps aux | grep "agent_main.py" | grep -v grep | awk '{print $2}' | xargs -r kill 2>/dev/null || true
    else
        # Alternative: kill by process name patterns
        kill $(jobs -p) 2>/dev/null || true
    fi
    echo "✨ Simulation complete."
}
trap cleanup EXIT

# --- Configuration ---
PARENT_DIR="./debate_runs"
CONFIG_DIR="./config"
TIMEOUT_DURATION=${TIMEOUT_DURATION:-600}  # Default 10 minutes, can be overridden

# --- Initialization ---
DEBATE_ID=$(date +'%Y%m%d-%H%M%S')
export DEBATE_DIR="${PARENT_DIR}/${DEBATE_ID}"
mkdir -p "${DEBATE_DIR}"
echo "🚀 Debate instance created at: ${DEBATE_DIR}"

# Initialize the message broker database
python3 message_broker.py init
echo "📬 Message Broker initialized."

# --- Agent Launch ---
AGENTS=("MODERATOR" "DEBATER_A" "DEBATER_N" "JUDGE_L" "JUDGE_E" "JUDGE_R" "ANALYST")
echo "🤖 Launching ${#AGENTS[@]} agents in the background..."

for AGENT in "${AGENTS[@]}"; do
  export AGENT_ID=${AGENT}
  python3 agent_main.py > "${DEBATE_DIR}/${AGENT}.log" 2>&1 &
  echo "   -> Launched ${AGENT}"
done

# Wait for agents to initialize
echo "⏳ Waiting for agents to initialize..."
sleep 3

# --- Debate Kickoff ---
echo "🏁 Kicking off the debate..."
INITIAL_MESSAGE='{"turn_id": 0, "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "sender_id": "SYSTEM", "recipient_id": "MODERATOR", "message_type": "START_DEBATE", "payload": {"content": "The debate may now begin. Topic: The impact of artificial intelligence on humanity."}}'

# Post the first message to the Moderator's queue
python3 message_broker.py post "MODERATOR" "${INITIAL_MESSAGE}"
echo "✅ Initial message sent to MODERATOR"

# --- Monitoring ---
echo "🗣️  Debate in progress. Monitoring logs in ${DEBATE_DIR}"
echo "📊 Starting real-time monitoring..."
echo "   Log files are being written to: ${DEBATE_DIR}/"
echo "   Message database: ${DEBATE_DIR}/messages.db"
echo "   Press Ctrl+C to stop the debate early"
echo "   Timeout: ${TIMEOUT_DURATION} seconds"

# Monitor the debate progress
START_TIME=$(date +%s)
LAST_PROGRESS_TIME=0

while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - START_TIME))
    
    # Check if timeout reached
    if [ $elapsed -ge $TIMEOUT_DURATION ]; then
        echo "⏰ TIMEOUT reached after ${TIMEOUT_DURATION} seconds. Shutting down."
        break
    fi
    
    # Show progress every 30 seconds
    if [ $((elapsed % 30)) -eq 0 ] && [ $elapsed -gt 0 ] && [ $elapsed -ne $LAST_PROGRESS_TIME ]; then
        LAST_PROGRESS_TIME=$elapsed
        echo "⏱️  Elapsed time: ${elapsed}s / ${TIMEOUT_DURATION}s"
        
        # Count total messages processed
        message_count=$(python3 -c "
import sqlite3
import os
db_file = os.path.join('${DEBATE_DIR}', 'messages.db')
try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM messages WHERE is_read = 1')
    result = cursor.fetchone()
    conn.close()
    print(result[0] if result else 0)
except:
    print(0)
" 2>/dev/null)
        echo "📨 Messages processed: ${message_count}"
        
        # Show agent activity (check if agents are still running)
        if command -v pgrep > /dev/null 2>&1; then
            active_agents=$(pgrep -f "agent_main.py" 2>/dev/null | wc -l)
        elif command -v ps > /dev/null 2>&1; then
            active_agents=$(ps aux | grep "agent_main.py" | grep -v grep | wc -l)
        else
            # Alternative: check background jobs
            active_agents=$(jobs | wc -l)
        fi
        echo "🤖 Active agents: ${active_agents}"
    fi
    
    sleep 5
done

echo "🔄 Final statistics and cleanup:"
# Generate final report using enhanced message broker
python3 -c "
import sqlite3
import os
import json

db_file = os.path.join('${DEBATE_DIR}', 'messages.db')
try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Count messages per agent
    cursor.execute('SELECT recipient_id, COUNT(*) FROM messages GROUP BY recipient_id')
    results = cursor.fetchall()
    
    print('📊 Message distribution:')
    for agent, count in results:
        print(f'   {agent}: {count} messages')
    
    # Count total processed messages
    cursor.execute('SELECT COUNT(*) FROM messages WHERE is_read = 1')
    processed = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM messages')
    total = cursor.fetchone()[0]
    
    print(f'📈 Processing rate: {processed}/{total} messages processed')
    
    # Show message types distribution
    cursor.execute('''
        SELECT json_extract(message_body, '$.message_type') as msg_type, 
               COUNT(*) as count 
        FROM messages 
        WHERE json_extract(message_body, '$.message_type') IS NOT NULL
        GROUP BY msg_type
    ''')
    msg_types = cursor.fetchall()
    
    if msg_types:
        print('📋 Message types:')
        for msg_type, count in msg_types:
            print(f'   {msg_type}: {count}')
    
    conn.close()
except Exception as e:
    print(f'❌ Error generating statistics: {e}')
"

echo ""
echo "📁 Results saved in: ${DEBATE_DIR}"
echo "   - Individual agent logs: *.log files"
echo "   - Message database: messages.db"
echo "   - Analysis report: debate_analysis_report.md (if generated)"
echo "   - Use 'python3 message_broker.py stats' in the debate directory for detailed stats"
echo ""
echo "🎯 To analyze results:"
echo "   cd ${DEBATE_DIR}"
echo "   python3 ../message_broker.py stats"
echo "   cat debate_analysis_report.md  # View analysis report"
