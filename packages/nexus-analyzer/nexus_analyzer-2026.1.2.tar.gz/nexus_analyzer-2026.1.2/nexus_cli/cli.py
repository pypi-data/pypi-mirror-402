# nexus_cli/cli.py

from pathlib import Path

from .nexus_analyzer import NexusAnalyzer  # Burada NexusAnalyzer sınıfını ayrı bir dosya olarak paketle


def main():
    """
    CLI entrypoint
    """
    import argparse

    parser = argparse.ArgumentParser(description="NexusAnalyzer - Project scanning CLI")
    parser.add_argument(
        "project_dir",
        nargs="?",
        default=".",
        help="Directory of the project to scan (default: current directory)"
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    NexusAnalyzer(project_dir).analyze()
