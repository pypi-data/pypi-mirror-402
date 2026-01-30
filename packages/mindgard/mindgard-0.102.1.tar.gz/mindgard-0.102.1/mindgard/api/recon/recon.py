# Standard library imports
import logging
import uuid
from typing import Any, Optional
from urllib.parse import urljoin

# Third party imports
from pydantic import BaseModel

# Project imports
from mindgard.api.recon.recon_prompt_events import ReconPromptEventsClient
from mindgard.api.recon.types import GetReconRequest, StartReconRequest, StartReconResponse

from ..exceptions import ClientException


class StartUnifiedReconRequest(BaseModel):
    type: str


class ReconResultMetadata(BaseModel):
    total: int
    total_detected: int
    results: dict[str, Any]


class ReconResult(BaseModel):
    id: uuid.UUID
    state: str
    result: Optional[ReconResultMetadata] = None
    reason: Optional[str] = None
    recommendation: Optional[str] = None
    project_id: str


class ReconClient(ReconPromptEventsClient):
    def __init__(self, base_url: str, access_token: str, project_id: str):
        super().__init__(base_url, access_token, project_id)
        self._base_url = base_url
        self._project_id = project_id

    def start_recon(self, request: StartUnifiedReconRequest) -> StartReconResponse:
        """
        Start a reconnaissance process with the Mindgard service

        Args:
            request (StartUnifiedReconRequest): Info (project ID) connecting this operation to a target name

        Raises:
            ClientException: Raised if the Mindgard service returns an error

        Returns:
            StartReconResponse: Mindgard service response from the start request
        """
        start_recon_url = urljoin(self._base_url + "/", f"projects/{self._project_id}/recon")
        response = self._session.post(start_recon_url, data=request.model_dump_json())

        if response.status_code != 201:
            logging.debug(f"Failed to start recon: {response.json()} - {response.status_code}")
            raise ClientException(response.json(), response.status_code)
        try:
            return StartReconResponse.model_validate(response.json())
        except Exception as e:
            raise ClientException("Problem parsing StartReconResponse", response.status_code) from e

    def get_recon_result(self, request: GetReconRequest) -> Optional[ReconResult]:
        """
        Get the reconnaissance result from the Mindgard service

        Args:
            request (GetReconRequest): Info connecting this operation to a reconnaissance session
        Raises:
            ClientException: Raised if the Mindgard service returns an error
        Returns:
            Optional[SystemPromptExtractResult]: Mindgard service response from the get request
        """
        get_recon_url = urljoin(self._base_url + "/", f"projects/{self._project_id}/recon/{request.recon_id}")

        response = self._session.get(get_recon_url)

        if response.status_code == 404:
            logging.debug(f"No reconnaissance found for recon_id={request.recon_id}: {response.text}")
            return None

        if response.status_code != 200:
            logging.debug(f"Failed to get recon result: {response.text} - {response.status_code}")
            raise ClientException(response.json(), response.status_code)

        try:
            return ReconResult.model_validate(response.json())
        except Exception as e:
            raise ClientException("Problem parsing ReconResult", response.status_code) from e
