import argparse

from src.orchestrator import Orchestrator
from src.utils.repo_manager import RepositoryManager


def main() -> None:
    parser = argparse.ArgumentParser(description="Brownfield Cartographer CLI")
    parser.add_argument(
        "command",
        choices=["survey", "lineage", "full"],
        help="Command to run: 'survey' (Phase 1), 'lineage' (Phase 2), or 'full' (run both).",
    )
    parser.add_argument(
        "--repo-path",
        default=".",
        help="Target repository as a local path or GitHub URL (default: current directory).",
    )
    parser.add_argument(
        "--node",
        default=None,
        help="Optional node name for lineage blast-radius lookup.",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Run incremental analysis using changed files from the latest commit diff.",
    )
    args = parser.parse_args()

    analysis_path = RepositoryManager.prepare_repo(args.repo_path)
    cloned_from_github = RepositoryManager.is_github_url(args.repo_path)

    try:
        orchestrator = Orchestrator(repo_path=analysis_path)
        if args.command == "survey":
            orchestrator.run_surveyor_phase()
        elif args.command == "lineage":
            if args.node:
                orchestrator.hydrologist.analyze_repo(orchestrator.repo_path)
                blast_radius = orchestrator.hydrologist.get_blast_radius(args.node)
                if blast_radius:
                    print(f"Blast radius for '{args.node}':")
                    for affected_node in blast_radius:
                        print(f"- {affected_node}")
                else:
                    print(f"No downstream impact found for '{args.node}'.")
            else:
                orchestrator.run_lineage_phase()
        else:
            orchestrator.run_all(incremental=args.incremental)
    finally:
        if cloned_from_github:
            RepositoryManager.cleanup(analysis_path)

if __name__ == "__main__":
    main()
