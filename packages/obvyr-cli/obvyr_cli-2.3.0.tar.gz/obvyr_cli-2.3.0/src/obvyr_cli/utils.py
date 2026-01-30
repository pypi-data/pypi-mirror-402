from importlib.metadata import version

import toml


def get_project_config(pyproject_path: str = "pyproject.toml") -> dict:
    try:
        with open(pyproject_path, "r") as file:
            config = toml.load(file)
            return config["tool"]["poetry"]
    except (KeyError, FileNotFoundError):
        # Fall back to package metadata for installed versions
        return {"version": version("obvyr-cli")}
