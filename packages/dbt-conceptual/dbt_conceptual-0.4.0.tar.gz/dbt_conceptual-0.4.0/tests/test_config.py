"""Tests for configuration loading."""

from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from dbt_conceptual.config import Config, RuleSeverity, ValidationConfig


def test_config_defaults() -> None:
    """Test that config loads with defaults."""
    with TemporaryDirectory() as tmpdir:
        config = Config.load(project_dir=Path(tmpdir))

        assert config.project_dir == Path(tmpdir)
        assert config.conceptual_path == "models/conceptual"
        assert config.silver_paths == ["models/silver"]
        assert config.gold_paths == ["models/gold"]
        # Check default validation config
        assert config.validation.orphan_models == RuleSeverity.WARN
        assert config.validation.unimplemented_concepts == RuleSeverity.WARN
        assert config.validation.unrealized_relationships == RuleSeverity.WARN
        assert config.validation.missing_definitions == RuleSeverity.IGNORE
        assert config.validation.domain_mismatch == RuleSeverity.WARN


def test_config_from_dbt_project() -> None:
    """Test that config loads from dbt_project.yml."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml with custom config
        dbt_project = {
            "name": "test",
            "vars": {
                "dbt_conceptual": {
                    "conceptual_path": "custom/conceptual",
                    "silver_paths": ["staging"],
                    "gold_paths": ["marts"],
                }
            },
        }

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump(dbt_project, f)

        config = Config.load(project_dir=tmppath)

        assert config.conceptual_path == "custom/conceptual"
        assert config.silver_paths == ["staging"]
        assert config.gold_paths == ["marts"]


def test_config_cli_overrides() -> None:
    """Test that CLI arguments override dbt_project.yml."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        dbt_project = {
            "name": "test",
            "vars": {
                "dbt_conceptual": {
                    "silver_paths": ["staging"],
                    "gold_paths": ["marts"],
                }
            },
        }

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump(dbt_project, f)

        # CLI overrides
        config = Config.load(
            project_dir=tmppath,
            silver_paths=["models/silver"],
            gold_paths=["models/gold"],
        )

        assert config.silver_paths == ["models/silver"]
        assert config.gold_paths == ["models/gold"]


def test_get_layer() -> None:
    """Test layer detection from path."""
    config = Config(
        project_dir=Path("/tmp"),
        silver_paths=["models/silver", "models/staging"],
        gold_paths=["models/gold", "models/marts"],
    )

    assert config.get_layer("models/silver/dim_customer") == "silver"
    assert config.get_layer("models/staging/stg_orders") == "silver"
    assert config.get_layer("models/gold/fact_orders") == "gold"
    assert config.get_layer("models/marts/fct_sales") == "gold"
    assert config.get_layer("models/other/something") is None


def test_get_model_type() -> None:
    """Test model type detection from name."""
    config = Config(project_dir=Path("/tmp"))

    assert config.get_model_type("dim_customer") == "dimension"
    assert config.get_model_type("fact_orders") == "fact"
    assert config.get_model_type("bridge_customer_segment") == "bridge"
    assert config.get_model_type("ref_calendar") == "reference"
    assert config.get_model_type("stg_customers") == "unknown"


def test_validation_config_from_dbt_project() -> None:
    """Test that validation config loads from dbt_project.yml."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml with validation config
        dbt_project = {
            "name": "test",
            "vars": {
                "dbt_conceptual": {
                    "validation": {
                        "orphan_models": "error",
                        "unimplemented_concepts": "ignore",
                        "missing_definitions": "warn",
                    }
                }
            },
        }

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump(dbt_project, f)

        config = Config.load(project_dir=tmppath)

        assert config.validation.orphan_models == RuleSeverity.ERROR
        assert config.validation.unimplemented_concepts == RuleSeverity.IGNORE
        assert config.validation.missing_definitions == RuleSeverity.WARN
        # These should remain at defaults
        assert config.validation.unrealized_relationships == RuleSeverity.WARN
        assert config.validation.domain_mismatch == RuleSeverity.WARN


def test_validation_config_defaults() -> None:
    """Test ValidationConfig dataclass defaults."""
    config = ValidationConfig()

    assert config.orphan_models == RuleSeverity.WARN
    assert config.unimplemented_concepts == RuleSeverity.WARN
    assert config.unrealized_relationships == RuleSeverity.WARN
    assert config.missing_definitions == RuleSeverity.IGNORE
    assert config.domain_mismatch == RuleSeverity.WARN
