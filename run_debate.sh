#!/bin/bash

# =================================================================
#  Unified Debate Orchestration Script (v5.0 - ReAct Integration)
#  統合ディベート実行スクリプト - ReActモデレータ対応版
# =================================================================

# --- Help Function ---
show_help() {
    echo "🎭 Unified Debate Orchestration Script (v5.0)"
    echo ""
    echo "USAGE:"
    echo "  $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help              Show this help message and exit"
    echo "  -t, --timeout SECONDS   Set debate timeout (default: 600)"
    echo "  -r, --react             Use ReAct moderator (default)"
    echo "  -c, --classic           Use classic/traditional moderator"
    echo "  -d, --debug             Enable debug mode with verbose output"
    echo ""
    echo "ENVIRONMENT VARIABLES:"
    echo "  USE_REACT_MODERATOR     Set to 'false' to use traditional moderator"
    echo "  TIMEOUT_DURATION        Debate timeout in seconds"
    echo "  USE_CLEAN_ARCHITECTURE  Enable Clean Architecture for agents"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                      # Run with ReAct moderator (default)"
    echo "  $0 --classic            # Run with traditional moderator"
    echo "  $0 --timeout 900        # Run with 15-minute timeout"
    echo "  USE_REACT_MODERATOR=false $0  # Traditional mode via env var"
    echo ""
    echo "OUTPUT:"
    echo "  Results are saved in: ./debate_runs/YYYYMMDD-HHMMSS/"
    echo "  - Agent logs: *.log files"
    echo "  - Message database: messages.db"
    echo "  - Analysis report: debate_analysis_report.md"
    echo ""
    exit 0
}

# --- Parse Command Line Arguments ---
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        -t|--timeout)
            TIMEOUT_DURATION="$2"
            shift 2
            ;;
        -r|--react)
            USE_REACT_MODERATOR=true
            shift
            ;;
        -c|--classic)
            USE_REACT_MODERATOR=false
            shift
            ;;
        -d|--debug)
            set -x  # Enable debug mode
            shift
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# --- Cleanup Function ---
cleanup() {
    echo "🧹 Cleaning up background processes..."
    # Kill both traditional and ReAct moderators
    if command -v pkill > /dev/null 2>&1; then
        pkill -f "react_moderator.py" 2>/dev/null || true
        pkill -f "agent_main.py" 2>/dev/null || true
    elif command -v ps > /dev/null 2>&1; then
        # Use ps if available
        ps aux | grep -E "(react_moderator|agent_main)" | grep -v grep | awk '{print $2}' | xargs -r kill 2>/dev/null || true
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
USE_REACT_MODERATOR=${USE_REACT_MODERATOR:-true}  # Default to ReAct moderator

# Show configuration
echo "🎭 Unified Debate Orchestration Script (v5.0)"
echo "================================================"
echo "⚙️  Configuration:"
echo "   🧠 Moderator Type: $([ "$USE_REACT_MODERATOR" = "true" ] && echo "ReAct (AI-powered)" || echo "Traditional (Rule-based)")"
echo "   ⏰ Timeout: ${TIMEOUT_DURATION} seconds"
echo "   🏗️  Architecture: $([ "${USE_CLEAN_ARCHITECTURE:-true}" = "true" ] && echo "Clean Architecture" || echo "Legacy")"
echo "   📁 Output Directory: ${PARENT_DIR}"
echo ""

# --- Initialization ---
DEBATE_ID=$(date +'%Y%m%d-%H%M%S')
export DEBATE_DIR="${PARENT_DIR}/${DEBATE_ID}"
mkdir -p "${DEBATE_DIR}"
echo "🚀 Debate instance created at: ${DEBATE_DIR}"

# Initialize the message broker database
echo "📬 Initializing Message Broker (Clean Architecture)..."
python3 -c "
from main.infrastructure.message_broker import SqliteMessageBroker
broker = SqliteMessageBroker()
broker.initialize_db()
print('Message Broker initialized successfully')
"

# --- Agent Launch ---
echo "🤖 Launching Clean Architecture debate system..."

# Launch all agents using the new CLI interface
AGENTS=("MODERATOR" "DEBATER_A" "DEBATER_N" "JUDGE_L" "JUDGE_E" "JUDGE_R" "ANALYST")
for AGENT in "${AGENTS[@]}"; do
    python3 -m main.interfaces.cli ${AGENT} --mode clean > "${DEBATE_DIR}/${AGENT}.log" 2>&1 &
    echo "   -> Launched ${AGENT} (Clean Architecture)"
done

# Wait for agents to initialize
echo "⏳ Waiting for agents to initialize..."
sleep 3

# --- Debate Kickoff ---
echo "🏁 Kicking off the debate..."

# Post the first message using Clean Architecture
python3 -c "
from main.infrastructure.message_broker import SqliteMessageBroker
from main.domain.models import Message
broker = SqliteMessageBroker()
message = Message(
    sender_id='SYSTEM',
    recipient_id='MODERATOR', 
    message_type='PROMPT_FOR_STATEMENT',
    payload={'topic': 'The impact of artificial intelligence on humanity'},
    turn_id=1
)
broker.post_message(message)
print('Initial message sent to MODERATOR')
"
echo "✅ Debate kickoff message sent to MODERATOR (Clean Architecture)"

# --- Monitoring ---
echo "🗣️  Clean Architecture debate in progress..."
echo "📊 Advanced ReAct system managing debate flow autonomously"

echo "   Log files are being written to: ${DEBATE_DIR}/"
echo "   Message database: ${DEBATE_DIR}/messages.db"
echo "   Press Ctrl+C to stop the debate early"
echo "   Timeout: ${TIMEOUT_DURATION} seconds"
echo ""

# --- Monitoring ---
echo " Starting real-time monitoring..."
START_TIME=$(date +%s)
LAST_PROGRESS_TIME=0
DEBATE_COMPLETED=false

while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - START_TIME))
    
    # Check if timeout reached
    if [ $elapsed -ge $TIMEOUT_DURATION ]; then
        echo "⏰ TIMEOUT reached after ${TIMEOUT_DURATION} seconds. Shutting down."
        break
    fi
    
    # Check for debate completion
    if [ "$DEBATE_COMPLETED" = "false" ]; then
        END_COUNT=$(python3 -c "
from main.infrastructure.message_broker import SqliteMessageBroker
import os
os.environ['DEBATE_DIR'] = '${DEBATE_DIR}'
try:
    broker = SqliteMessageBroker()
    history = broker.get_all_messages()
    end_count = sum(1 for msg in history if msg.message_type == 'END_DEBATE')
    print(end_count)
except Exception as e:
    print(0)
" 2>/dev/null)
        if [ "$END_COUNT" -gt 0 ]; then
            echo "🏁 END_DEBATE message detected. Clean Architecture debate completed!"
            DEBATE_COMPLETED=true
            sleep 5  # Give agents time to shut down gracefully
            break
        fi
    fi
    
    # Show progress every 30 seconds
    if [ $((elapsed % 30)) -eq 0 ] && [ $elapsed -gt 0 ] && [ $elapsed -ne $LAST_PROGRESS_TIME ]; then
        LAST_PROGRESS_TIME=$elapsed
        echo "⏱️  Elapsed time: ${elapsed}s / ${TIMEOUT_DURATION}s"
        
        # Count total messages processed
        message_count=$(python3 -c "
from main.infrastructure.message_broker import SqliteMessageBroker
import os
os.environ['DEBATE_DIR'] = '${DEBATE_DIR}'
try:
    broker = SqliteMessageBroker()
    stats = broker.get_statistics()
    print(stats['total_messages'])
except Exception as e:
    print(0)
" 2>/dev/null)
        echo "📨 Messages processed: ${message_count}"
        
        # Show agent activity
        if command -v pgrep > /dev/null 2>&1; then
            active_agents=$(pgrep -f -c "main.interfaces.cli" 2>/dev/null || echo 0)
        elif command -v ps > /dev/null 2>&1; then
            active_agents=$(ps aux | grep "main.interfaces.cli" | grep -v grep | wc -l)
        else
            active_agents=$(jobs | wc -l)
        fi
        echo "🤖 Active agents: ${active_agents}"
        
        # Show message type distribution
        msg_types=$(python3 -c "
import sqlite3
import os
import json
db_file = os.path.join('${DEBATE_DIR}', 'messages.db')
try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT json_extract(message_body, '$.message_type') as msg_type, 
               COUNT(*) as count 
        FROM messages 
        WHERE json_extract(message_body, '$.message_type') IS NOT NULL
        GROUP BY msg_type
        ORDER BY count DESC
        LIMIT 5
    ''')
    results = cursor.fetchall()
    conn.close()
    if results:
        types = [f'{t}:{c}' for t, c in results]
        print(' | '.join(types))
    else:
        print('No message types found')
except:
    print('Stats unavailable')
" 2>/dev/null)
        echo "📋 Top message types: ${msg_types}"
    fi
    
    sleep 5
done

# Wait for graceful shutdown
if [ "$DEBATE_COMPLETED" = "true" ]; then
    echo "⏳ Waiting for agents to complete graceful shutdown..."
    sleep 5
fi

echo ""
echo "🔄 Final statistics and cleanup:"

# Generate comprehensive final report
python3 -c "
import sqlite3
import os
import json

print('='*60)
print('🎭 DEBATE SESSION SUMMARY')
print('='*60)

db_file = os.path.join('${DEBATE_DIR}', 'messages.db')
moderator_type = 'ReAct' if '${USE_REACT_MODERATOR}' == 'true' else 'Traditional'
print(f'📊 Moderator Type: {moderator_type}')
print(f'📁 Session Directory: ${DEBATE_DIR}')
print()

try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Count messages per agent
    cursor.execute('SELECT recipient_id, COUNT(*) FROM messages GROUP BY recipient_id ORDER BY COUNT(*) DESC')
    results = cursor.fetchall()
    
    print('� Message Distribution by Agent:')
    total_messages = 0
    for agent, count in results:
        print(f'   📤 {agent}: {count} messages')
        total_messages += count
    print(f'   📈 Total: {total_messages} messages')
    print()
    
    # Count total processed messages
    cursor.execute('SELECT COUNT(*) FROM messages WHERE is_read = 1')
    processed = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM messages')
    total = cursor.fetchone()[0]
    
    processing_rate = (processed / total * 100) if total > 0 else 0
    print(f'⚡ Processing Statistics:')
    print(f'   ✅ Processed: {processed}/{total} messages ({processing_rate:.1f}%)')
    print()
    
    # Show detailed message types distribution
    cursor.execute('''
        SELECT json_extract(message_body, '$.message_type') as msg_type, 
               COUNT(*) as count 
        FROM messages 
        WHERE json_extract(message_body, '$.message_type') IS NOT NULL
        GROUP BY msg_type
        ORDER BY count DESC
    ''')
    msg_types = cursor.fetchall()
    
    if msg_types:
        print('📋 Message Types Breakdown:')
        for msg_type, count in msg_types:
            percentage = (count / total_messages * 100) if total_messages > 0 else 0
            print(f'   🔸 {msg_type}: {count} ({percentage:.1f}%)')
        print()
    
    # Timeline analysis
    cursor.execute('''
        SELECT json_extract(message_body, '$.timestamp') as timestamp,
               json_extract(message_body, '$.message_type') as msg_type,
               json_extract(message_body, '$.sender_id') as sender
        FROM messages 
        WHERE timestamp IS NOT NULL
        ORDER BY timestamp
        LIMIT 10
    ''')
    timeline = cursor.fetchall()
    
    if timeline:
        print('⏰ Debate Timeline (First 10 Messages):')
        for i, (timestamp, msg_type, sender) in enumerate(timeline, 1):
            print(f'   {i:2d}. {timestamp} | {sender:10s} | {msg_type}')
        print()
    
    # Check for completion indicators
    cursor.execute('''
        SELECT COUNT(*) FROM messages 
        WHERE json_extract(message_body, '$.message_type') = 'END_DEBATE'
    ''')
    end_count = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM messages 
        WHERE json_extract(message_body, '$.message_type') = 'ANALYSIS_REPORT_COMPLETE'
    ''')
    analysis_count = cursor.fetchone()[0]
    
    print('🏁 Completion Status:')
    print(f'   🛑 END_DEBATE signals: {end_count}')
    print(f'   📄 Analysis reports: {analysis_count}')
    print()
    
    conn.close()
    
except Exception as e:
    print(f'❌ Error generating statistics: {e}')
    print()

print('='*60)
"

echo ""
echo "📁 Results saved in: ${DEBATE_DIR}"
echo "   - Individual agent logs: *.log files"
echo "   - Message database: messages.db"
if [ -f "${DEBATE_DIR}/debate_analysis_report.md" ]; then
    echo "   - Analysis report: debate_analysis_report.md ✅"
else
    echo "   - Analysis report: debate_analysis_report.md (pending)"
fi

echo ""
echo "🎯 To analyze results further:"
echo "   cd ${DEBATE_DIR}"
echo "   python3 ../message_broker.py stats    # Detailed message statistics"
if [ -f "${DEBATE_DIR}/debate_analysis_report.md" ]; then
    echo "   cat debate_analysis_report.md      # View generated analysis"
fi

echo ""
if [ "$USE_REACT_MODERATOR" = "true" ]; then
    echo "🧠 ReAct Moderator Session Complete!"
    echo "   The ReAct moderator used reasoning and action cycles"
    echo "   to autonomously manage the debate flow."
else
    echo "🏛️  Traditional Moderator Session Complete!"
    echo "   The traditional moderator followed state-based transitions."
fi

echo ""
echo "✨ Debate orchestration finished successfully!"
