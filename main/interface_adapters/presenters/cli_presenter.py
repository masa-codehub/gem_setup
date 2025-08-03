"""
CLI Presenter - プレゼンテーション層（Green Phase）
"""
import argparse


class CLIPresenter:
    """CLI表示ロジックを担当するプレゼンター"""

    @staticmethod
    def parse_arguments():
        """コマンドライン引数を解析"""
        description = "AI Agent Main Controller"
        parser = argparse.ArgumentParser(description=description)
        parser.add_argument("agent_id", help="The ID of the agent to run")
        parser.add_argument(
            "--mode",
            choices=['clean', 'legacy'],
            default='clean',
            help="Execution mode"
        )
        return parser.parse_args()

    @staticmethod
    def display_startup_message(agent_id: str, mode: str):
        """起動メッセージを表示"""
        print(f"Starting agent {agent_id} in {mode} mode...")

    @staticmethod
    def display_error_message(error: str):
        """エラーメッセージを表示"""
        print(f"Error: {error}")
