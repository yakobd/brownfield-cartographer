import argparse

from src.orchestrator import Orchestrator


def main() -> None:
    parser = argparse.ArgumentParser(description="Brownfield Cartographer CLI")
    parser.add_argument(
        "command",
        choices=["survey", "lineage"],
        help="Command to run. Use 'survey' for Phase 1 or 'lineage' for lineage graph.",
    )
    parser.add_argument(
        "--repo-path",
        default=".",
        help="Path to the target repository (default: current directory).",
    )
    parser.add_argument(
        "--node",
        default=None,
        help="Optional node name for lineage blast-radius lookup.",
    )
    args = parser.parse_args()

    orchestrator = Orchestrator(repo_path=args.repo_path)
    if args.command == "survey":
        orchestrator.run_surveyor_phase()
    else:
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

if __name__ == "__main__":
    main()
