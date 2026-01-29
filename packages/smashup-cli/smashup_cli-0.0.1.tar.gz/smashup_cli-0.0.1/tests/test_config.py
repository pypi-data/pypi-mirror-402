from pathlib import Path

import pytest

from smashup import config


@pytest.fixture()
def temp_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "factions.toml")
    return tmp_path


def test_ensure_config_creates_default(temp_config_dir: Path) -> None:
    config.ensure_config()

    assert config.CONFIG_FILE.exists()
    data = config._read_config_data()
    assert data.get("version") == config.CONFIG_VERSION
    assert "expansions" in data


def test_load_config_reads_enabled_flags(temp_config_dir: Path) -> None:
    config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config.CONFIG_FILE.write_text(
        "\n".join(
            [
                "version = 2",
                "",
                "[[expansions]]",
                "name = \"Alpha\"",
                "enabled = true",
                "factions = [\"One\", \"Two\"]",
                "",
                "[[expansions]]",
                "name = \"Beta\"",
                "enabled = false",
                "factions = [\"Three\"]",
                "",
            ]
        ),
        encoding="utf-8",
    )

    expansions = config.load_config()

    assert len(expansions) == 2
    assert expansions[0].enabled is True
    assert expansions[1].enabled is False


def test_load_config_rejects_invalid_enabled(temp_config_dir: Path) -> None:
    config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config.CONFIG_FILE.write_text(
        "\n".join(
            [
                "version = 2",
                "",
                "[[expansions]]",
                "name = \"Bad\"",
                "enabled = \"yes\"",
                "factions = [\"One\"]",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        config.load_config()


def test_ensure_config_preserves_enabled_on_upgrade(
    temp_config_dir: Path,
) -> None:
    config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config.CONFIG_FILE.write_text(
        "\n".join(
            [
                "version = 1",
                "",
                "[[expansions]]",
                "name = \"Core Set\"",
                "enabled = false",
                "factions = [\"Aliens\", \"Dinosaurs\"]",
                "",
            ]
        ),
        encoding="utf-8",
    )

    config.ensure_config()
    expansions = config.load_config()

    core = next(
        expansion for expansion in expansions if expansion.name == "Core Set"
    )
    assert core.enabled is False
