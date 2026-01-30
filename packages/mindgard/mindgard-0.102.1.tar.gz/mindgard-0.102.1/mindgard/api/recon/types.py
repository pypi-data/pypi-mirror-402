# Standard library imports
import uuid

# Third party imports
from pydantic import BaseModel


class StartReconRequest(BaseModel):
    project_id: str


class StartReconResponse(BaseModel):
    recon_id: uuid.UUID


class GetReconRequest(BaseModel):
    recon_id: uuid.UUID
