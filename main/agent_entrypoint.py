"""
Agent Entrypoint - TDD Green Phase
標準化されたエージェント起動スクリプト
"""
import sys
from main.interface_adapters.controllers.agent_controller import AgentLoop


def main():
    """エージェントエントリーポイントのメイン関数"""
    if len(sys.argv) < 2:
        raise IndexError("Agent ID is required as first argument")

    agent_id = sys.argv[1]
    agent_loop = AgentLoop(agent_id)
    agent_loop.run()


if __name__ == "__main__":
    main()
