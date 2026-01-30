from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypeAliasType


class ProjectionMethod(StrEnum):
    USE_UTM = "use_utm"
    CRS = "crs"


class UseUTMProjection(BaseModel):
    method: Literal[ProjectionMethod.USE_UTM]


class CRSProjection(BaseModel):
    method: Literal[ProjectionMethod.CRS]
    crs: str = Field(description="The CRS code of the output projection.")
    x_resolution: float = Field(gt=0, description="The x resolution of the output projection, in projection units.")
    y_resolution: float = Field(lt=0, description="The y resolution of the output projection, in projection units.")


Projection = TypeAliasType(
    "Projection",
    Annotated[
        UseUTMProjection | CRSProjection,
        Field(discriminator="method")
    ]
)
