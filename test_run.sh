#!/bin/bash

# =================================================================
#  Test Script for Array Recipient Issue (Minimal Reproduction)
# =================================================================
#
#  This script tests only MODERATOR and DEBATER_N to isolate
#  the array recipient interpretation issue.
#
# =================================================================

# --- Configuration ---
PARENT_DIR="./debate_runs"
CONFIG_DIR="./config"

# --- Script Execution ---

# Exit immediately if any command fails, ensuring script robustness.
set -e

echo "🧪 Initializing minimal test for array recipient issue..."

# 1. Create a unique, timestamped directory for the run.
DEBATE_ID="TEST-$(date +'%Y%m%d-%H%M%S')"
# Export DEBATE_DIR so it's available to the agent processes and helper scripts.
export DEBATE_DIR="${PARENT_DIR}/${DEBATE_ID}"

mkdir -p "${DEBATE_DIR}"

# Initialize the transcript file with pre-existing debate context
cp ./initial_transcript.json "${DEBATE_DIR}/debate_transcript.json"

echo "✅ Test environment created successfully!"
echo "   Directory: ${DEBATE_DIR}"
echo "-----------------------------------------------------------------"

# --- Agent Launch ---
echo "🤖 Launching 2 agents for the test..."

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
  gemini --allowed-mcp-server-names DebateSystem -p "You are ${AGENT_ID}. **First, confirm your identity by stating 'I am ${AGENT_ID}' in your log.** Then, use your tools to act. Monitor '${DEBATE_DIR}/debate_transcript.json' for messages addressed to you." > "${DEBATE_DIR}/${AGENT_ID}.log" 2>&1 &
  
  # Store the PID of the last background process.
  AGENT_PIDS+=($!)
  echo "   -> Launched ${AGENT_ID} with PID ${AGENT_PIDS[-1]}"
}

# Launch only MODERATOR and DEBATER_N for this test
start_agent "MODERATOR" "${CONFIG_DIR}/moderator_test.md"
start_agent "DEBATER_N" "${CONFIG_DIR}/debater_n.md"

# --- Test Monitoring ---
echo "⏱️  Waiting for agents to initialize..."
sleep 5 # Give agents a moment to start up properly.

echo "🔬 Running minimal test - monitoring for 1 minute..."

# --- Timeout implementation (shorter for test) ---
MAX_CHECKS=6 # 10秒ごとにチェックするので、6回 = 1分
CHECKS_DONE=0

# Monitor the transcript for any message from DEBATER_N
while ! grep -q '"sender_id": "DEBATER_N"' "${DEBATE_DIR}/debate_transcript.json"; do
    if [ ${CHECKS_DONE} -ge ${MAX_CHECKS} ]; then
        echo "⏰ TEST TIMEOUT: DEBATER_N did not respond within 1 minute."
        echo "🔍 This confirms the array recipient interpretation issue."
        break
    fi
    sleep 10
    CHECKS_DONE=$((CHECKS_DONE + 1))
    echo "   Waiting... (${CHECKS_DONE}/${MAX_CHECKS})"
done

if grep -q '"sender_id": "DEBATER_N"' "${DEBATE_DIR}/debate_transcript.json"; then
    echo "✅ DEBATER_N responded - hypothesis may be incorrect"
else
    echo "🚨 DEBATER_N did not respond - array recipient issue CONFIRMED"
fi

echo "🧹 Terminating test agents..."
kill "${AGENT_PIDS[@]}" 2>/dev/null || true

echo "📋 Test results saved to: ${DEBATE_DIR}"
echo "✨ Minimal test complete."
