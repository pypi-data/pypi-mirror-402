from platformdirs import user_config_dir
from pathlib import Path
import click
import json

APP_NAME = "codeppr"

def get_config_dir() -> Path:
    """
    Returns the OS-correct global config file path.
    """
    config_dir = Path(user_config_dir(APP_NAME))
    return config_dir / "config.json"

def set_default_config() -> None:
    config_file = get_config_dir()
    config_file.parent.mkdir(parents=True, exist_ok=True)

    if not config_file.exists():
        default_config = {
            "provider": "openai",
            "model": "gpt-4.1",
        }

        with config_file.open("w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)

def read_config() -> dict[str, str]:
    config_file = get_config_dir()

    if not config_file.exists():
        set_default_config()

    try:
        with config_file.open("r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError:
        click.secho("Error: Configuration file is corrupted. Resetting to default configuration.", fg="red", bold=True)
        set_default_config()
        return {}
    except Exception as e:
        click.secho(f"Error reading configuration file: {e}", fg="red", bold=True)
        return {}

    return config

def write_config(config: dict[str, str]) -> None:
    config_file = get_config_dir()
    config_file.parent.mkdir(parents=True, exist_ok=True)

    tmp = config_file.with_suffix(".tmp")

    with tmp.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    tmp.replace(config_file)