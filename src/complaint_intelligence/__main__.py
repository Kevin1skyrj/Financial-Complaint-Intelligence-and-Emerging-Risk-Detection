"""Command-line status summary for the implemented complaint-intelligence project."""

from pathlib import Path

from complaint_intelligence.config import load_config


def main() -> None:
    config = load_config()
    model_path = Path(config["model"]["artifact_path"])
    evaluation_path = Path(config["model"]["evaluation_report_path"])
    dashboard_path = Path("powerbi/Financial_Complaint_Intelligence.pbix")

    completed_artifacts = sum(
        path.exists() for path in (model_path, evaluation_path, dashboard_path)
    )

    print("Financial Complaint Intelligence")
    print(f"Status: implemented locally ({completed_artifacts}/3 release artifacts available)")
    print(f"Prepared data: {config['data']['prepared_path']}")
    print(f"Classification baseline: {config['model']['name']}")
    print(f"Model artifact: {model_path}")
    print(f"Evaluation report: {evaluation_path}")
    print(f"Power BI report: {dashboard_path}")


if __name__ == "__main__":
    main()

