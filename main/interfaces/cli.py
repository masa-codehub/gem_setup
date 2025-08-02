"""
CLI エントリーポイント - 最小限の実装（Green phase）
"""
import argparse
from main.interfaces.agent_orchestrator import AgentOrchestrator


def main():
    """CLIのメインエントリーポイント"""
    parser = argparse.ArgumentParser(description="AI Agent Main Controller")
    parser.add_argument("agent_id", help="The ID of the agent to run")
    parser.add_argument(
        "--mode",
        choices=['clean', 'legacy'],
        default='clean',
        help="Execution mode"
    )

    args = parser.parse_args()

    orchestrator = AgentOrchestrator(args.agent_id, args.mode)
    orchestrator.start()


if __name__ == "__main__":
    main()
