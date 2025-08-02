#!/bin/bash

# =================================================================
#  Master Orchestration Script (v2.0 - Event-Driven)
# =================================================================

# --- Configuration ---
PARENT_DIR="./debate_runs"
CONFIG_DIR="./config"

set -e

# --- Initialization ---
DEBATE_ID=$(date +'%Y%m%d-%H%M%S')
export DEBATE_DIR="${PARENT_DIR}/${DEBATE_ID}"
mkdir -p "${DEBATE_DIR}"
TRANSCRIPT_FILE="${DEBATE_DIR}/debate_transcript.json"
touch "${TRANSCRIPT_FILE}"

echo "🚀 Debate instance created at: ${DEBATE_DIR}"

# --- Helper Functions ---

# Safely appends a message to the transcript using a lock file
write_message() {
  local message=$1
  (
    flock -x 200
    echo "${message}" >> "${TRANSCRIPT_FILE}"
  ) 200>"${DEBATE_DIR}/transcript.lock"
}

# Wakes up a specific agent to get its response
invoke_agent() {
  local agent_id=$1
  local context=$2
  
  # For now, we'll create a simple mock response for testing
  # In production, this would call the actual AI service
  local turn_id=$(wc -l < "${TRANSCRIPT_FILE}")
  local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  
  echo "⚠️  MOCK MODE: Agent ${agent_id} would process: ${context}"
  
  # Mock different responses based on agent and context
  case "${agent_id}" in
    "MODERATOR")
      if echo "${context}" | grep -q "START_DEBATE"; then
        echo "{\"turn_id\": ${turn_id}, \"timestamp\": \"${timestamp}\", \"sender_id\": \"${agent_id}\", \"recipient_id\": \"DEBATER_A\", \"message_type\": \"PROMPT_FOR_STATEMENT\", \"payload\": {\"content\": \"Please provide your opening statement.\"}}"
      else
        echo "{\"turn_id\": ${turn_id}, \"timestamp\": \"${timestamp}\", \"sender_id\": \"${agent_id}\", \"recipient_id\": \"SYSTEM\", \"message_type\": \"END_DEBATE\", \"payload\": {\"content\": \"Debate concluded.\"}}"
      fi
      ;;
    "DEBATER_A")
      echo "{\"turn_id\": ${turn_id}, \"timestamp\": \"${timestamp}\", \"sender_id\": \"${agent_id}\", \"recipient_id\": \"MODERATOR\", \"message_type\": \"SUBMIT_STATEMENT\", \"payload\": {\"content\": \"This is my opening statement supporting the affirmative position.\"}}"
      ;;
    "DEBATER_N")
      echo "{\"turn_id\": ${turn_id}, \"timestamp\": \"${timestamp}\", \"sender_id\": \"${agent_id}\", \"recipient_id\": \"MODERATOR\", \"message_type\": \"SUBMIT_STATEMENT\", \"payload\": {\"content\": \"This is my opening statement opposing the position.\"}}"
      ;;
    *)
      echo "{\"turn_id\": ${turn_id}, \"timestamp\": \"${timestamp}\", \"sender_id\": \"${agent_id}\", \"recipient_id\": \"MODERATOR\", \"message_type\": \"MOCK_RESPONSE\", \"payload\": {\"content\": \"This is a mock response from ${agent_id}\"}}"
      ;;
  esac
}

# --- Main Debate Loop ---

# Kick off the debate
INITIAL_MESSAGE='{"turn_id": 0, "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "sender_id": "SYSTEM", "recipient_id": "MODERATOR", "message_type": "START_DEBATE", "payload": {"content": "The debate may now begin."}}'
write_message "${INITIAL_MESSAGE}"
echo "🏁 Debate started."

TURN_COUNT=1
MAX_TURNS=30 # Set a max number of turns to prevent infinite loops

while [ ${TURN_COUNT} -lt ${MAX_TURNS} ]; do
  echo "--- Turn ${TURN_COUNT} ---"
  
  # 1. Get the last message to determine who should act next
  LAST_MESSAGE=$(tail -n 1 "${TRANSCRIPT_FILE}")
  RECIPIENT=$(echo "${LAST_MESSAGE}" | jq -r '.recipient_id')
  MESSAGE_TYPE=$(echo "${LAST_MESSAGE}" | jq -r '.message_type')

  # 2. Check for the end of the debate
  if [ "${MESSAGE_TYPE}" == "END_DEBATE" ]; then
    echo "✅ END_DEBATE message received. Concluding simulation."
    break
  fi

  # 3. Determine the next agent to invoke
  # For simplicity, we'll invoke the recipient directly.
  # A more complex system could parse the message type.
  NEXT_AGENT=${RECIPIENT}
  
  echo "🗣️  Invoking ${NEXT_AGENT}..."

  # 4. Invoke the agent and get its response
  # We pass the last message as the primary context.
  AGENT_RESPONSE=$(invoke_agent "${NEXT_AGENT}" "${LAST_MESSAGE}")

  # 5. Write the agent's response to the transcript
  if [ -n "${AGENT_RESPONSE}" ]; then
    write_message "${AGENT_RESPONSE}"
    echo "   -> ${NEXT_AGENT} responded."
  else
    echo "⚠️  Agent ${NEXT_AGENT} did not respond. Ending debate."
    break
  fi
  
  TURN_COUNT=$((TURN_COUNT + 1))
  sleep 1 # A small delay to prevent rapid-fire requests
done

if [ ${TURN_COUNT} -ge ${MAX_TURNS} ]; then
    echo "⏰ TIMEOUT: Maximum turn count reached."
fi

echo "✨ Simulation complete."