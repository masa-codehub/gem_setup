#!/bin/bash

# =================================================================
#  Master Orchestration Script for 6-Agent Debate System (v1.0)
# =================================================================
#
#  This script manages the full lifecycle of the debate simulation:
#  1. Creates a unique environment for the run.
#  2. Launches 6 AI agents as background processes.
#  3. Kicks off the debate by sending the initial message.
#  4. Monitors the debate for its conclusion.
#  5. Cleans up all processes upon completion.
#
# =================================================================

# --- Configuration ---
PARENT_DIR="./debate_runs"
CONFIG_DIR="./config"

# --- Script Execution ---

# Exit immediately if any command fails, ensuring script robustness.
set -e

echo "🚀 Initializing new debate instance..."

# 1. Create a unique, timestamped directory for the run.
DEBATE_ID=$(date +'%Y%m%d-%H%M%S')
# Export DEBATE_DIR so it's available to the agent processes and helper scripts.
export DEBATE_DIR="${PARENT_DIR}/${DEBATE_ID}"

mkdir -p "${DEBATE_DIR}"

# Initialize the transcript file.
touch "${DEBATE_DIR}/debate_transcript.json"

echo "✅ Debate environment created successfully!"
echo "   Directory: ${DEBATE_DIR}"
echo "-----------------------------------------------------------------"

# --- Agent Launch ---
echo "🤖 Launching 6 agents in the background..."
# Array to store the Process IDs (PIDs) of the background agents.
AGENT_PIDS=()

# Function to launch a single agent.
start_agent() {
  local AGENT_ID=$1
  local GEMINI_MD_PATH=$2
  # All agents use the same system-level prompt.
  local SYSTEM_MD_PATH="${CONFIG_DIR}/debate_system.md"

  # Set environment variables for the gemini-cli process.
  export AGENT_ID
  export GEMINI_SYSTEM_MD="${SYSTEM_MD_PATH}"
  export GEMINI_MD="${GEMINI_MD_PATH}"

  # Launch gemini-cli as a background process (&).
  # The initial prompt orients the agent and includes a self-check.
  # stdout and stderr are redirected to a log file for later analysis.
  # UPDATED: Use MCP server configured in settings.json
  gemini --allowed-mcp-server-names DebateSystem -p "You are ${AGENT_ID}. **First, confirm your identity by stating 'I am ${AGENT_ID}' in your log.** Then, use your tools to act. Monitor '${DEBATE_DIR}/debate_transcript.json' for messages addressed to you." > "${DEBATE_DIR}/${AGENT_ID}.log" 2>&1 &
  
  # Store the PID of the last background process.
  AGENT_PIDS+=($!)
  echo "   -> Launched ${AGENT_ID} with PID ${AGENT_PIDS[-1]}"
}

# Launch all 6 agents with their respective strategic personas.
start_agent "MODERATOR" "${CONFIG_DIR}/moderator.md"
start_agent "DEBATER_A" "${CONFIG_DIR}/debater_a.md"
start_agent "DEBATER_N" "${CONFIG_DIR}/debater_n.md"
start_agent "JUDGE_L"   "${CONFIG_DIR}/judge_l.md"
start_agent "JUDGE_E"   "${CONFIG_DIR}/judge_e.md"
start_agent "JUDGE_R"   "${CONFIG_DIR}/judge_r.md"

# --- Debate Kickoff ---
echo "⏱️  Waiting for agents to initialize..."
sleep 5 # Give agents a moment to start up properly.

echo "🏁 Kicking off the debate by sending the first message..."
# Construct the initial message as a JSON string.
# The timestamp is generated dynamically.
INITIAL_MESSAGE='{"turn_id": 0, "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "sender_id": "SYSTEM", "recipient_id": "MODERATOR", "message_type": "START_DEBATE", "payload": {"content": "The debate may now begin."}}'

# Use direct file write for the initial system message (not from an agent).
echo "${INITIAL_MESSAGE}" >> "${DEBATE_DIR}/debate_transcript.json"

# --- Monitoring and Cleanup ---
echo "🗣️ Debate in progress. Monitoring for completion..."
echo "   (Check agent logs in ${DEBATE_DIR} for details)"

# --- NEW: Timeout implementation ---
MAX_CHECKS=60 # 10秒ごとにチェックするので、60回 = 10分
CHECKS_DONE=0

# Monitor the transcript for the "END_DEBATE" message from the Moderator.
while ! grep -q '"message_type": "END_DEBATE"' "${DEBATE_DIR}/debate_transcript.json"; do
    if [ ${CHECKS_DONE} -ge ${MAX_CHECKS} ]; then
        echo "⏰ TIMEOUT: Debate did not conclude within the time limit (10 minutes). Forcing termination."
        break # ループを抜ける
    fi
    sleep 10 # Check every 10 seconds
    CHECKS_DONE=$((CHECKS_DONE + 1))
done

echo "✅ Debate has concluded or timed out. Terminating all agent processes..."
# Send a kill signal to all stored PIDs to clean up.
kill "${AGENT_PIDS[@]}" 2>/dev/null || true # エラーを無視

echo "✨ Simulation complete."