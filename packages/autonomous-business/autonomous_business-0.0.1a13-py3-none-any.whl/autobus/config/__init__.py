from pathlib import Path
import tomllib
import os


def load_config():

    config_file_path = None
    cwd_config_path = os.path.join(Path.cwd(), 'autobus.toml')
    home_dir_config_path = os.path.join(os.path.expanduser("~"), '.autobus', 'autobus.toml')

    # 1. Look in the current working directory as a last resort (for local development)
    if os.path.exists(cwd_config_path):
        print("autobus.toml in cwd is used.")
        config_file_path = Path(cwd_config_path)

    # 2. Look in the user's home directory: ~/.autobus/autobus.toml
    elif os.path.exists(home_dir_config_path):
        print("~/.autobus/autobus.toml is used.")
        config_file_path = Path(home_dir_config_path)

    # 3. Use default in the config module
    else:
        print("Warning: No configuration file found in working directory or ~/.autobus/autobus.toml. Using defaults.")
        config_file_path = Path(__file__).parent / "autobus.toml"

    with config_file_path.open(mode="rb") as fp:
        config = tomllib.load(fp)
        return config


config = load_config()
