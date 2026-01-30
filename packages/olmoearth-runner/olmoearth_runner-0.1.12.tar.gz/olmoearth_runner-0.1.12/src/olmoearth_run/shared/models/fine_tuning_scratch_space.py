from pydantic import BaseModel, Field

from olmoearth_run.shared.models.model_stage_paths import ModelStagePaths


OLMOEARTH_CONFIG_FILE_NAME = "olmoearth_config.yaml"


class FineTuningScratchSpace(BaseModel):
    root_path: str = Field(description="The root directory of the scratch space")

    @property
    def olmoearth_config_path(self) -> str:
        return f"{self.root_path}/{OLMOEARTH_CONFIG_FILE_NAME}"

    @property
    def model_stage_paths(self) -> ModelStagePaths:
        """This is the model stage actively being created and trained in this scratch space."""
        return ModelStagePaths(root_path=self.root_path)

    # TODO chrisw:
    # After dropping legacy config, we can move ft workflow-specific
    # paths out of ModelStagePaths and into this class.
