# ============================
# == STRATEGY: MODERATOR (TEST) ==
# ============================
#
# YOUR GOAL:
# Test the array recipient functionality by sending a single message to both DEBATER_A and DEBATER_N.

# YOUR CORE LOGIC: SIMPLIFIED TEST STATE MACHINE

# -- STATE DEFINITIONS --

# 1. AWAITING_START
#    - Condition: The transcript contains the `START_DEBATE` message or messages from DEBATER_A.
#    - Action: Send a single `STATEMENT_FOR_REVIEW` message to both DEBATER_A and DEBATER_N using array recipient format: `["DEBATER_A", "DEBATER_N"]`. Then, immediately send an `END_DEBATE` message.

# YOUR MESSAGE TYPES FOR THIS TEST:
# - `STATEMENT_FOR_REVIEW` (with array recipient)
# - `END_DEBATE`

# CRITICAL TEST BEHAVIOR:
# You must send exactly ONE message with recipient_id as an array: ["DEBATER_A", "DEBATER_N"]
# This is the core functionality we are testing.
# The message should contain DEBATER_A's statement for review by both debaters.

# EXAMPLE MESSAGE FORMAT:
# {
#   "turn_id": 3,
#   "timestamp": "2025-07-31T10:00:00Z",
#   "sender_id": "MODERATOR",
#   "recipient_id": ["DEBATER_A", "DEBATER_N"],
#   "message_type": "STATEMENT_FOR_REVIEW",
#   "payload": {
#     "content": "Please review the following opening statement from DEBATER_A: [statement content]"
#   }
# }

# After sending this test message, immediately end the debate to conclude the test.
