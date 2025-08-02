#!/bin/bash

# ===============================================================
#  Simplified Debate Orchestration Script (ReAct Version)
# ===============================================================

# --- Cleanup Function ---
cleanup() {
    echo "🧹 Cleaning up background processes..."
    pkill -f "react_moderator.py" 2>/dev/null || true
    pkill -f "simple_agent.py" 2>/dev/null || true
    echo "✨ Simulation complete."
}
trap cleanup EXIT

# --- Configuration ---
PARENT_DIR="./debate_runs"
TIMEOUT_DURATION=${TIMEOUT_DURATION:-600}  # Default 10 minutes

# --- Initialization ---
DEBATE_ID=$(date +'%Y%m%d-%H%M%S')
export DEBATE_DIR="${PARENT_DIR}/${DEBATE_ID}"
mkdir -p "${DEBATE_DIR}"
echo "🚀 Debate instance created at: ${DEBATE_DIR}"

# Initialize the message broker database
python3 -c "import message_broker; message_broker.initialize_db()"
echo "📬 Message Broker initialized at ${DEBATE_DIR}/messages.db"

# --- Agent Launch ---
echo "🤖 Launching ReAct-based debate system..."

# Launch ReAct Moderator
export AGENT_ID="MODERATOR"
python3 react_moderator.py > "${DEBATE_DIR}/MODERATOR.log" 2>&1 &
echo "   -> Launched ReAct MODERATOR"

# Launch other agents using simple_agent.py
OTHER_AGENTS=("DEBATER_A" "DEBATER_N" "JUDGE_L" "JUDGE_E" "JUDGE_R" "ANALYST")
for AGENT in "${OTHER_AGENTS[@]}"; do
  export AGENT_ID=${AGENT}
  python3 simple_agent.py > "${DEBATE_DIR}/${AGENT}.log" 2>&1 &
  echo "   -> Launched ${AGENT}"
done

# Wait for agents to initialize
echo "⏳ Waiting for agents to initialize..."
sleep 3

# --- Debate Kickoff ---
echo "🏁 Kicking off the debate..."
INITIAL_MESSAGE='{"turn_id": 0, "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "sender_id": "SYSTEM", "recipient_id": "MODERATOR", "message_type": "START_DEBATE", "payload": {"content": "The debate may now begin. Topic: The impact of artificial intelligence on humanity."}}'

# Post the first message to the Moderator's queue
python3 -c "
import message_broker
import json
message = json.loads('${INITIAL_MESSAGE}')
message_broker.post_message('MODERATOR', message)
"
echo "✅ Initial message sent to ReAct MODERATOR"

# --- Monitoring ---
echo "🗣️  ReAct-based debate in progress..."
echo "📊 The MODERATOR will now autonomously manage the debate flow"
echo "   Log files: ${DEBATE_DIR}/"
echo "   Message database: ${DEBATE_DIR}/messages.db"
echo "   Press Ctrl+C to stop the debate early"
echo "   Timeout: ${TIMEOUT_DURATION} seconds"

# Simple monitoring loop
START_TIME=$(date +%s)
LAST_CHECK_TIME=0

while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - START_TIME))
    
    # Check if timeout reached
    if [ $elapsed -ge $TIMEOUT_DURATION ]; then
        echo "⏰ TIMEOUT reached after ${TIMEOUT_DURATION} seconds. Shutting down."
        break
    fi
    
    # Show progress every 30 seconds
    if [ $((elapsed % 30)) -eq 0 ] && [ $elapsed -gt 0 ] && [ $elapsed -ne $LAST_CHECK_TIME ]; then
        LAST_CHECK_TIME=$elapsed
        echo "⏱️  Elapsed time: ${elapsed}s / ${TIMEOUT_DURATION}s"
        
        # Check if any END_DEBATE messages have been sent
        END_COUNT=$(python3 -c "
import sqlite3
import json
import os
db_file = os.path.join('${DEBATE_DIR}', 'messages.db')
try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute(\"SELECT message_body FROM messages WHERE message_body LIKE '%END_DEBATE%'\")
    results = cursor.fetchall()
    conn.close()
    print(len(results))
except:
    print(0)
" 2>/dev/null)
        
        if [ "$END_COUNT" -gt 0 ]; then
            echo "🏁 END_DEBATE message detected. Debate completed!"
            sleep 5  # Give agents time to shut down gracefully
            break
        fi
        
        # Show message statistics
        MSG_COUNT=$(python3 -c "
import sqlite3
import os
db_file = os.path.join('${DEBATE_DIR}', 'messages.db')
try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM messages')
    result = cursor.fetchone()
    conn.close()
    print(result[0] if result else 0)
except:
    print(0)
" 2>/dev/null)
        
        echo "   Total messages processed: ${MSG_COUNT}"
    fi
    
    sleep 5
done

# Wait a bit for graceful shutdown
echo "⏳ Waiting for graceful shutdown..."
sleep 5

echo "🎭 Debate session completed!"
echo "📁 Results saved in: ${DEBATE_DIR}"

# Show final statistics
if [ -f "${DEBATE_DIR}/messages.db" ]; then
    echo ""
    echo "📊 Final Statistics:"
    python3 message_broker.py stats 2>/dev/null || echo "   Statistics unavailable"
fi

# Check if analysis report was generated
if [ -f "${DEBATE_DIR}/debate_analysis_report.md" ]; then
    echo "📄 Analysis report available: ${DEBATE_DIR}/debate_analysis_report.md"
fi

echo "✨ All done!"
