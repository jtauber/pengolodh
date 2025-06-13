import tomllib

from xdg_base_dirs import xdg_config_home


CONFIG_FILE = xdg_config_home() / "pengolodh.toml"


if CONFIG_FILE.exists():
    with open(CONFIG_FILE, "rb") as f:
        configuration = tomllib.load(f)
else:
    configuration = {}


def books_configuration() -> dict:
    return configuration.get("books", {})
