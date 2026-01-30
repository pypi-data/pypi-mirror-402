from upath import UPath


from olmoearth_shared.models.olmoearth_config.olmoearth_config import OlmoEarthConfig
from olmoearth_run.shared.models.olmoearth_run_config import OlmoEarthRunConfig
from olmoearth_run.runner.tools.olmoearth_run_config_loader import OlmoEarthRunConfigLoader


class ConfigClassLoader:
    @staticmethod
    def load_olmoearth_run_config(config_path: str) -> OlmoEarthRunConfig:
        """Loads legacy OlmoEarthRunConfig from a YAML file into pydantic runtime object"""
        return OlmoEarthRunConfigLoader.load_olmoearth_run_config(config_path)

    @staticmethod
    def load_olmoearth_config(config_path: str) -> OlmoEarthConfig:
        """Loads unified OlmoEarthConfig from a YAML file into pydantic runtime object"""
        with UPath(config_path).open('r') as file:
            yaml_content = file.read()
        return OlmoEarthConfig.from_yaml(yaml_content)
