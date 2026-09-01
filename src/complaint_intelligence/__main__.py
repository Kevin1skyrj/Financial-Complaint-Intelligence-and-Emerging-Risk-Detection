"""Small smoke-test entry point; model training is a later milestone."""

from complaint_intelligence.config import load_config


def main() -> None:
    config = load_config()
    print("Financial Complaint Intelligence")
    print("Status: initial scaffold; no trained model yet")
    print(f"Planned raw data: {config['data']['raw_path']}")
    print(f"Planned baseline: {config['model']['name']}")


if __name__ == "__main__":
    main()

