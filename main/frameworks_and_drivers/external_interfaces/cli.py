"""
CLI エントリーポイント - 最小限の実装（Green phase）
"""
import argparse


class CLI:
    """CLIメインクラス（Green Phase実装）"""

    def __init__(self):
        self.agent_orchestrator = None

    def run(self):
        """CLIのメインエントリーポイント"""
        description = "AI Agent Main Controller"
        parser = argparse.ArgumentParser(description=description)
        parser.add_argument("agent_id", help="The ID of the agent to run")
        parser.add_argument(
            "--mode",
            choices=['clean', 'legacy'],
            default='clean',
            help="Execution mode"
        )

        args = parser.parse_args()

        # Dynamic import to avoid circular dependency
        from main.interface_adapters.controllers.agent_orchestrator import AgentOrchestrator
        orchestrator = AgentOrchestrator(args.agent_id, args.mode)
        orchestrator.start()


def main():
    """CLIのメインエントリーポイント"""
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()
