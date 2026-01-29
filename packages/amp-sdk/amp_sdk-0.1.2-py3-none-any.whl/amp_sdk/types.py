from __future__ import annotations

"""Type definitions for the Amp Python SDK."""

import json
from typing import (
    Any,
    Literal,
    Optional,
    Union,
)

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ============================================================================
# Content Block Types
# ============================================================================


class TextContent(BaseModel):
    """Text content block."""

    type: Literal["text"] = "text"
    text: str


class ToolUseContent(BaseModel):
    """Tool use content block."""

    type: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: dict[str, Any]


class ToolResultContent(BaseModel):
    """Tool result content block."""

    type: Literal["tool_result"] = "tool_result"
    tool_use_id: str
    content: str
    is_error: bool = False


# ============================================================================
# Usage Information Types
# ============================================================================


class Usage(BaseModel):
    """Token usage information."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    service_tier: Optional[str] = None


# ============================================================================
# Message Types
# ============================================================================


# Private
class _MCPServerStatus(BaseModel):
    """MCP server status information."""

    name: str
    status: Literal["connected", "connecting", "connection-failed", "disabled"]


class _AssistantMessageDetails(BaseModel):
    """Assistant message payload."""

    id: Optional[str] = None
    type: Literal["message"] = "message"
    role: Literal["assistant"] = "assistant"
    model: Optional[str] = None
    content: list[Union[TextContent, ToolUseContent]]
    stop_reason: Optional[Literal["end_turn", "tool_use", "max_tokens"]] = None
    stop_sequence: Optional[str] = None
    usage: Optional[Usage] = None


class _UserMessageDetails(BaseModel):
    """User message payload."""

    role: Literal["user"] = "user"
    content: list[Union[TextContent, ToolResultContent]]


# Public
class BaseMessage(BaseModel):
    """Base message with common fields."""

    model_config = ConfigDict(extra="allow")

    type: str
    session_id: str


class SystemMessage(BaseMessage):
    """System initialization message."""

    type: Literal["system"] = "system"
    subtype: Literal["init"] = "init"
    cwd: str
    tools: list[str]
    mcp_servers: list[_MCPServerStatus]


class AssistantMessage(BaseMessage):
    """Assistant response message."""

    type: Literal["assistant"] = "assistant"
    message: _AssistantMessageDetails
    parent_tool_use_id: Optional[str] = None


class UserMessage(BaseMessage):
    """User input message."""

    type: Literal["user"] = "user"
    message: _UserMessageDetails
    parent_tool_use_id: Optional[str] = None


class ResultMessage(BaseMessage):
    """Success result message."""

    type: Literal["result"] = "result"
    subtype: Literal["success"] = "success"
    is_error: Literal[False] = False
    result: str
    duration_ms: int
    num_turns: int
    usage: Optional[Usage] = None
    permission_denials: Optional[list[str]] = None


class ErrorResultMessage(BaseMessage):
    """Error result message."""

    type: Literal["result"] = "result"
    subtype: Literal["error_during_execution", "error_max_turns"] = "error_during_execution"
    is_error: Literal[True] = True
    error: str
    duration_ms: int
    num_turns: int
    usage: Optional[Usage] = None
    permission_denials: Optional[list[str]] = None


StreamMessage = Union[
    SystemMessage, AssistantMessage, UserMessage, ResultMessage, ErrorResultMessage
]


# ============================================================================
# User Message Types
# ============================================================================


# Private
class _UserInputMessageDetails(BaseModel):
    """User input message payload."""

    role: Literal["user"] = "user"
    content: list[Union[TextContent, ToolResultContent]] = Field(default_factory=list)


# Public
class UserInputMessage(BaseModel):
    """User input message for streaming."""

    type: Literal["user"] = Field("user", description="Message type identifier")
    message: _UserInputMessageDetails = Field(
        default_factory=_UserInputMessageDetails,
        description="Message payload containing role and content",
    )


# ============================================================================
# Permission Types
# ============================================================================

PermissionMatchCondition = Union[
    str,
    bool,
    int,
    float,
    None,
    list["PermissionMatchCondition"],
    dict[str, "PermissionMatchCondition"],
]


class Permission(BaseModel):
    """Permission rule for tool usage."""

    tool: str = Field(
        ..., min_length=1, description="The name of the tool to which this entry applies"
    )
    matches: Optional[dict[str, Any]] = Field(None, description="Maps tool inputs to conditions")
    action: Literal["allow", "reject", "ask", "delegate"] = Field(
        ..., description="How Amp should proceed in case of a match"
    )
    context: Optional[Literal["thread", "subagent"]] = Field(
        None, description="Only apply this entry in this context"
    )
    to: Optional[str] = Field(
        None, min_length=1, description='Command to delegate to when action is "delegate"'
    )

    @model_validator(mode="after")
    def validate_delegate_action(self) -> Permission:
        """Validate that delegate action has 'to' field."""
        if self.action == "delegate" and not self.to:
            raise ValueError('delegate action requires "to" field')
        if self.action != "delegate" and self.to:
            raise ValueError('"to" field only allowed with delegate action')
        return self


PermissionsList = list[Permission]


# ============================================================================
# MCP Types
# ============================================================================


class MCPServer(BaseModel):
    """MCP server configuration."""

    command: str
    args: list[str] = Field(
        default_factory=list, description="Command line arguments to pass to the MCP server"
    )
    env: dict[str, str] = Field(
        default_factory=dict,
        description="Environment variables to set for the MCP server process",
    )
    disabled: Optional[bool] = Field(False, description="Whether this server is disabled")


class MCPConfig(BaseModel):
    """
    MCP configuration as a top-level mapping of server names to server configs.

    Matches TypeScript SDK format: { "server-name": { command, args?, env?, disabled? } }

    Example:
        {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                "env": {}
            }
        }
    """

    servers: dict[str, MCPServer] = Field(
        default_factory=dict,
        description="Mapping of server names to MCP server configurations",
    )

    def to_json_string(self) -> str:
        """
        Convert to JSON string for CLI argument.
        Returns top-level map format: {"server-name": {...}}
        """
        return json.dumps(
            {
                name: server.model_dump(exclude_defaults=True)
                for name, server in self.servers.items()
            },
            separators=(",", ":"),
        )


# ============================================================================
# Execute Types
# ============================================================================


class AmpOptions(BaseModel):
    """Configuration options for Amp execution."""

    model_config = ConfigDict(populate_by_name=True)

    cwd: Optional[str] = None
    mode: Literal["smart", "rush", "large"] = Field(
        default="smart",
        description="Agent mode - controls the model, system prompt, and tool selection",
    )
    dangerously_allow_all: bool = Field(default=False, alias="dangerouslyAllowAll")
    visibility: Optional[Literal["private", "public", "workspace", "group"]] = "workspace"
    settings_file: Optional[str] = Field(default=None, alias="settingsFile")
    log_level: Optional[Literal["debug", "info", "warn", "error", "audit"]] = Field(
        default=None, alias="logLevel"
    )
    log_file: Optional[str] = Field(default=None, alias="logFile")
    env: dict[str, str] = Field(default_factory=dict)
    continue_thread: Union[bool, str, None] = Field(default=None, alias="continue")
    mcp_config: Optional[Union[MCPConfig, str]] = Field(default=None, alias="mcpConfig")
    toolbox: Optional[str] = Field(default=None, description="Folder path with toolbox scripts")
    skills: Optional[str] = Field(
        default=None, description="Folder path with custom skills"
    )
    permissions: Optional[PermissionsList] = Field(
        default=None, description="Permission rules for tool usage"
    )

    @field_validator("mcp_config")
    @classmethod
    def validate_mcp_config(
        cls, v: Union[MCPConfig, dict[str, Any], str, None]
    ) -> Optional[Union[MCPConfig, str]]:
        """
        Validate MCP configuration.
        Accepts dict in top-level map format: {"server-name": {...}}
        """
        if isinstance(v, dict):
            return MCPConfig(servers=v)
        return v
