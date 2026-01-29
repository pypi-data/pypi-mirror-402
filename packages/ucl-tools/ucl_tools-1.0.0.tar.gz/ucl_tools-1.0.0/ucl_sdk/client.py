from typing import Optional, Any
import requests

from .types import Tool, ExecuteToolResponse

BASE_URL = "https://live.fastn.ai/api/ucl"


class UCLClient:
    def __init__(
        self,
        space_id: str,
        tenant_id: str = "",
        gateway_id: Optional[str] = None,
        api_key: Optional[str] = None,
        auth_token: Optional[str] = None,
    ):
        if not space_id:
            raise ValueError("space_id is required")

        if not api_key and not auth_token:
            raise ValueError("Either api_key or auth_token is required")

        self._space_id = space_id
        self._tenant_id = tenant_id
        self._gateway_id = gateway_id if gateway_id else space_id
        self._api_key = api_key
        self._auth_token = auth_token

    def _get_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "x-fastn-space-id": self._space_id,
            "x-fastn-space-tenantid": self._tenant_id,
            "x-fastn-space-agent-id": self._gateway_id,
            "stage": "LIVE",
        }

        if self._api_key:
            headers["x-fastn-api-key"] = self._api_key

        if self._auth_token:
            headers["authorization"] = self._auth_token

        return headers

    def get_tools(self, limit: int = 10, prompt: Optional[str] = None) -> list[Tool]:
        input_data: dict[str, Any] = {
            "limit": limit,
            "version": "v2",
        }

        if prompt:
            input_data["prompt"] = prompt

        response = requests.post(
            f"{BASE_URL}/getTools",
            headers=self._get_headers(),
            json={"input": input_data},
        )

        response.raise_for_status()
        return response.json()

    def execute_tool(
        self, tool_name: str, parameters: Optional[dict[str, Any]] = None
    ) -> ExecuteToolResponse:
        if not tool_name:
            raise ValueError("tool_name is required")

        response = requests.post(
            f"{BASE_URL}/executeTool",
            headers=self._get_headers(),
            json={
                "input": {
                    "toolName": tool_name,
                    "parameters": parameters or {},
                }
            },
        )

        response.raise_for_status()
        return response.json()
