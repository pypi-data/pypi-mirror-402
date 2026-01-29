"""
Amp Python SDK

This SDK provides a Python interface to the Amp CLI, allowing you to
run Amp programmatically in Python applications. It wraps the Amp CLI
with the --stream-json flag to provide structured output.
"""

from .core import create_permission, create_user_message, execute
from .exceptions import (
    AmpError,
    AmpTimeoutError,
    CancellationError,
    CLINotFoundError,
    ProcessError,
    ValidationError,
)
from .types import (
    AmpOptions,
    AssistantMessage,
    ErrorResultMessage,
    MCPConfig,
    MCPServer,
    Permission,
    PermissionMatchCondition,
    PermissionsList,
    ResultMessage,
    StreamMessage,
    SystemMessage,
    TextContent,
    ToolResultContent,
    ToolUseContent,
    Usage,
    UserInputMessage,
    UserMessage,
)

# ============================================================================
# Package Metadata
# ============================================================================

__version__ = "0.1.0"
__author__ = "Amp"
__email__ = "dev@ampcode.com"

# ============================================================================
# Public API
# ============================================================================

__all__ = [
    # Core functions
    "execute",
    "create_user_message",
    "create_permission",
    # Execute types
    "AmpOptions",
    # Message types
    "StreamMessage",
    "SystemMessage",
    "AssistantMessage",
    "UserMessage",
    "ResultMessage",
    "ErrorResultMessage",
    "UserInputMessage",
    # Content types
    "TextContent",
    "ToolUseContent",
    "ToolResultContent",
    # Usage types
    "Usage",
    # MCP types
    "MCPConfig",
    "MCPServer",
    # Permission types
    "Permission",
    "PermissionsList",
    "PermissionMatchCondition",
    # Exceptions
    "AmpError",
    "CLINotFoundError",
    "ProcessError",
    "ValidationError",
    "AmpTimeoutError",
    "CancellationError",
]
