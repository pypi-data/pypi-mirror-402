from typing import TypedDict, Optional, Any


class Tool(TypedDict):
    name: str
    description: str
    inputSchema: dict[str, Any]


class ExecuteToolResponse(TypedDict):
    body: dict[str, Any]
    rawBody: str
    statusCode: int
