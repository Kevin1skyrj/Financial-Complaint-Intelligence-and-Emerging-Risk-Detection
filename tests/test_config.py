from pathlib import Path

import pytest

from complaint_intelligence.config import load_config


def test_baseline_config_has_required_sections() -> None:
    config = load_config(Path("configs/baseline.yaml"))

    assert {"project", "data", "split", "model"}.issubset(config)
    assert config["data"]["text_column"] == "Consumer complaint narrative"
    assert config["model"]["name"] == "tfidf_logistic_regression"


def test_missing_config_has_clear_error(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.yaml"

    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        load_config(missing_path)

