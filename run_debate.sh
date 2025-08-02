#!/bin/bash

# =================================================================
#  Master Orchestration Script for 6-Agent Debate System (v1.2)
# =================================================================
#
#  This script now relies on gemini-cli to manage the MCP server.
#
# =================================================================

# --- Configuration ---
PARENT_DIR="./debate_runs"
CONFIG_DIR="./config"

# --- Cleanup Function ---
cleanup() {
    echo "🧹 Cleaning up background processes..."
    # kill 0 sends the signal to all processes in the current process group.
    kill 0 || true
}
trap cleanup EXIT

# --- Script Execution ---
set -e

echo "🚀 Initializing new debate instance..."

DEBATE_ID=$(date +'%Y%m%d-%H%M%S')
export DEBATE_DIR="${PARENT_DIR}/${DEBATE_ID}"
mkdir -p "${DEBATE_DIR}"
touch "${DEBATE_DIR}/debate_transcript.json"

echo "✅ Debate environment created successfully!"
echo "   Directory: ${DEBATE_DIR}"
echo "-----------------------------------------------------------------"

# --- Agent Launch ---
# The MCP server will be started automatically by the first gemini agent that needs it.
echo "🤖 Launching 7 agents in the background..."

start_agent() {
  local AGENT_ID=$1
  local GEMINI_MD_PATH=$2
  local SYSTEM_MD_PATH="${CONFIG_DIR}/debate_system.md"

  export AGENT_ID
  export GEMINI_SYSTEM_MD="${SYSTEM_MD_PATH}"
  export GEMINI_MD="${GEMINI_MD_PATH}"

  # The --allowed-mcp-server-names flag tells gemini which server from settings.json to use.
  # Gemini will handle starting the server on the first use.
  gemini --allowed-mcp-server-names DebateSystem -p "You are ${AGENT_ID}. Confirm your identity by stating 'I am ${AGENT_ID}' in your log, then use your tools to act. Monitor '${DEBATE_DIR}/debate_transcript.json'." > "${DEBATE_DIR}/${AGENT_ID}.log" 2>&1 &
}

# Launch all 7 agents
start_agent "MODERATOR" "${CONFIG_DIR}/moderator.md"
start_agent "DEBATER_A" "${CONFIG_DIR}/debater_a.md"
start_agent "DEBATER_N" "${CONFIG_DIR}/debater_n.md"
start_agent "JUDGE_L"   "${CONFIG_DIR}/judge_l.md"
start_agent "JUDGE_E"   "${CONFIG_DIR}/judge_e.md"
start_agent "JUDGE_R"   "${CONFIG_DIR}/judge_r.md"
start_agent "ANALYST"   "${CONFIG_DIR}/analyst.md"

# --- Debate Kickoff ---
echo "🏁 Kicking off the debate..."
sleep 5 # Wait for agents to initialize

INITIAL_MESSAGE='{"turn_id": 0, "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "sender_id": "SYSTEM", "recipient_id": "MODERATOR", "message_type": "START_DEBATE", "payload": {"content": "The debate may now begin."}}'

# The MODERATOR agent is now responsible for processing the START_DEBATE message.
# We no longer need a special command to write the initial message.
echo "${INITIAL_MESSAGE}" >> "${DEBATE_DIR}/debate_transcript.json"

# --- Monitoring ---
echo "🗣️ Debate in progress. Monitoring for completion..."
MAX_CHECKS=60 # 10 minutes timeout
CHECKS_DONE=0

while ! grep -q '"message_type": "END_DEBATE"' "${DEBATE_DIR}/debate_transcript.json"; do
    if [ ${CHECKS_DONE} -ge ${MAX_CHECKS} ]; then
        echo "⏰ TIMEOUT: Debate did not conclude within the time limit."
        break
    fi
    sleep 10
    CHECKS_DONE=$((CHECKS_DONE + 1))
done

echo "✅ Debate has concluded or timed out."
echo "✨ Simulation complete."
# The 'trap cleanup EXIT' will handle the termination of all processes.