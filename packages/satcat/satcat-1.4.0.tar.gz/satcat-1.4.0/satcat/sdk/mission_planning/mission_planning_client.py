import json
import os
from io import StringIO
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Collection,
    Dict,
    List,
    Optional,
    TextIO,
    Union,
)
from urllib.parse import urljoin

from satcat.sdk.mission_planning import models
from satcat.sdk.settings import settings
from satcat.sdk.utils import (
    PathLike,
    SortDirection,
    open_path_or_buf,
    poll_job_for_completion,
    poll_job_for_completion_percent_generator,
    remove_none_vals,
)

if TYPE_CHECKING:
    from satcat.sdk.client import Client


class MissionPlanningClient:
    client: "Client"

    def __init__(self, client: "Client"):
        self.client = client

    def list_visibility_windows(
        self,
        config: models.VisibilityWindowsRequest,
    ) -> models.VisibilityWindowsResult:
        """
        """
        data = config.dict()
        params = {}
        path = urljoin(settings.satcat_rest_api_url, "visibility_windows")
        res = self.client.request_authenticated(
            path, json=data, method="POST", params=params
        )
        windows_result = models.VisibilityWindowsResult.parse_obj(res.json())

        return windows_result