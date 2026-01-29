# Amp Python SDK

Use the Amp SDK to programmatically deploy the Amp agent anywhere you run Python. Execute Amp CLI commands programmatically with full type safety, streaming responses, and complete control over your AI coding agent workflows.

## Why use the Amp SDK?

The Amp Python SDK brings the Amp agent directly into your applications with simple, reliable functionality:

- **Stream Inputs**: Send prompts and messages incrementally to the Amp agent
- **Stream Outputs**: Receive structured JSON responses (system, assistant, result) as the agent executes tasks
- **Multi-turn Conversations**: Maintain back-and-forth interactions across multiple executions
- **Thread Continuity**: Continue an existing thread (latest or by ID) to build stateful agent workflows
- **Programmatic Settings**: Configure working directories, settings, and tools without user prompts — ideal for automation
- **MCP Integration**: Extend Amp with custom Model Context Protocol servers and tools
- **Custom Skills**: Define and use custom agent skills to extend Amp's functionality

## What can you build?

The Amp SDK enables a wide range of AI-powered applications:

### Development Tools

- **Code Review Agent**: Automated pull request analysis and feedback
- **Documentation Generator**: Create and maintain project documentation
- **Test Automation**: Generate and execute test suites
- **Migration Assistant**: Help upgrade codebases and refactor legacy code

### Workflow Automation

- **CI/CD Integration**: Smart build and deployment pipelines
- **Issue Triage**: Automatically categorize and prioritize bug reports
- **Code Quality Monitoring**: Continuous analysis of code health metrics
- **Release Management**: Automated changelog generation and version bumping

## Quick Start

### Installation

```bash
# Install the Amp SDK using pip
pip install amp-sdk

# Install the Amp Core using npm
npm install -g @sourcegraph/amp
```

Once installed, add your API key to the environment. You can access your API key at [ampcode.com/settings](https://ampcode.com/settings).

```bash
export AMP_API_KEY=sgamp_your_api_key_here
```

### Your First Amp Command

Now that you have the SDK installed and your API key set up, you can start using Amp with the `execute()` function:

```python
import asyncio
from amp_sdk import execute

async def main():
    # Simple execution - get the final result
    async for message in execute("What files are in this directory?"):
        if message.type == "result" and not message.is_error:
            print("Result:", message.result)
            break

asyncio.run(main())
```

The `execute()` function only requires that you provide a `prompt` to get started. The SDK streams messages as the agent works, letting you handle responses and integrate them directly into your application.

## Core Concepts

### Message Streaming

The SDK streams different types of messages as your agent executes:

```python
from amp_sdk import execute

async def main():
    async for message in execute("Run tests"):
        if message.type == "system":
            # Session info, available tools, MCP servers
            print("Available tools:", message.tools)
        elif message.type == "assistant":
            # AI responses and tool usage
            print("Assistant is working...")
        elif message.type == "result":
            # Final result (success or error)
            print("Done:", message.result)

asyncio.run(main())
```

### Simple Result Extraction

When you just need the final result without handling streaming:

```python
import asyncio
from amp_sdk import execute, AmpOptions

async def get_result(prompt: str) -> str:
    async for message in execute(prompt, AmpOptions(dangerously_allow_all=True)):
        if message.type == "result":
            if message.is_error:
                raise Exception(message.error)
            return message.result
    raise Exception("No result received")

# Usage
async def main():
    try:
        result = await get_result("List all Python files in this project")
        print("Found files:", result)
    except Exception as error:
        print("Failed:", str(error))

asyncio.run(main())
```

### Thread Continuity

Continue conversations across multiple interactions:

```python
from amp_sdk import execute, AmpOptions

async def main():
    # Continue the most recent conversation
    async for message in execute(
        "What was the last error you found?",
        AmpOptions(continue_thread=True)
    ):
        if message.type == "result":
            print(message.result)

    # Continue a specific thread by ID
    async for message in execute(
        "Can you update that code we discussed?",
        AmpOptions(continue_thread="T-abc123-def456")
    ):
        if message.type == "result":
            print(message.result)

asyncio.run(main())
```

## Common Configuration

### Skip Permission Prompts

For automation scenarios, bypass permission prompts:

```python
from amp_sdk import execute, AmpOptions

async def main():
    async for message in execute(
        "Make changes without asking for permission",
        AmpOptions(dangerously_allow_all=True)
    ):
        # Handle messages...
        pass

asyncio.run(main())
```

### Working Directory

Specify where Amp should run:

```python
from amp_sdk import execute, AmpOptions

async def main():
    async for message in execute(
        "Refactor the auth module",
        AmpOptions(cwd="./my-project")
    ):
        # Process messages...
        pass

asyncio.run(main())
```

### Enable Debug Logging

See what's happening under the hood:

```python
from amp_sdk import execute, AmpOptions

async def main():
    async for message in execute(
        "Analyze this project",
        AmpOptions(
            log_level="debug",  # Shows CLI command in console
            log_file="./amp-debug.log"  # Optional: write logs to file
        )
    ):
        # Process messages
        pass

asyncio.run(main())
```

### Agent Mode

Select which agent mode to use. The mode controls the model, system prompt, and tool selection:

```python
from amp_sdk import execute, AmpOptions

async def main():
    async for message in execute(
        "Quickly fix this typo",
        AmpOptions(mode="rush")  # Use rush mode for faster responses
    ):
        # Process messages
        pass

asyncio.run(main())
```

Available modes:

- **smart** (default): Balanced mode with full capabilities
- **rush**: Faster responses with streamlined tool usage
- **large**: 1M-token long-context workhorse

### Tool Permissions

Control which tools Amp can use with fine-grained permissions:

```python
from amp_sdk import execute, AmpOptions, create_permission

async def main():
    async for message in execute(
        "List files and run tests",
        AmpOptions(
            permissions=[
                # Allow listing files
                create_permission("Bash", "allow", {"matches": {"cmd": "ls *"}}),
                # Allow running tests
                create_permission("Bash", "allow", {"matches": {"cmd": "npm test"}}),
                # Ask before reading sensitive files
                create_permission("Read", "ask", {"matches": {"path": "/etc/*"}}),
            ]
        )
    ):
        # Process messages
        pass

asyncio.run(main())
```

Permission rules support:

- **Pattern matching**: Use `*` wildcards and regex patterns
- **Context control**: Restrict rules to main thread or sub-agents
- **Delegation**: Delegate permission decisions to external programs

Learn more about permissions in the [manual](https://ampcode.com/manual#permissions) and the [appendix](https://ampcode.com/manual/appendix#permissions-reference).

## Advanced Usage

### Interactive Progress Tracking

For building user interfaces that show real-time progress:

```python
from amp_sdk import execute

async def execute_with_progress(prompt: str):
    print("Starting task...")

    async for message in execute(prompt):
        if message.type == "system" and message.subtype == "init":
            print("Tools available:", ", ".join(message.tools))
        elif message.type == "assistant":
            # Show tool usage or assistant responses
            content = message.message.content[0]
            if content.type == "tool_use":
                print(f"Using {content.name}...")
            elif content.type == "text":
                print("Assistant:", content.text[:100] + "...")
        elif message.type == "result":
            if message.is_error:
                print("Failed:", message.error)
            else:
                print("Completed successfully!")
                print(message.result)
```

### Cancellation and Timeouts

Handle long-running operations gracefully:

```python
import asyncio
from amp_sdk import execute, AmpOptions

async def execute_with_timeout(prompt: str, timeout_seconds: float = 30.0):
    try:
        async for message in asyncio.wait_for(
            execute(prompt, AmpOptions(dangerously_allow_all=True)),
            timeout=timeout_seconds
        ):
            if message.type == "result":
                return message.result
    except asyncio.TimeoutError:
        raise Exception(f"Operation timed out after {timeout_seconds}s")
```

### MCP (Model Context Protocol) Integration

Extend Amp's capabilities with custom tools and data sources:

```python
from amp_sdk import execute, AmpOptions
from amp_sdk.types import MCPConfig, MCPServer

async def main():
    mcp_config = MCPConfig(
        servers={
            "playwright": MCPServer(
                command="npx",
                args=["-y", "@playwright/mcp@latest", "--headless"],
                env={"NODE_ENV": "production"}
            ),
            "database": MCPServer(
                command="node",
                args=["./custom-mcp-server.js"],
                env={"DB_CONNECTION_STRING": os.environ.get("DATABASE_URL")}
            )
        }
    )

    async for message in execute(
        "Test the login flow on staging environment",
        AmpOptions(
            mcp_config=mcp_config,
            dangerously_allow_all=True
        )
    ):
        if message.type == "system":
            print(
                "MCP Servers:",
                [(s.name, s.status) for s in message.mcp_servers]
            )
        # Handle other messages...

asyncio.run(main())
```

To find out more about extending Amp with MCP servers, visit the [MCP Configuration](https://ampcode.com/manual#mcp) section of the manual.

### Multi-turn Conversations

Build streaming conversations using async generators:

```python
import asyncio
from amp_sdk import execute, create_user_message

async def generate_messages():
    yield create_user_message("Start analyzing the codebase")

    # Wait for some condition or user input
    await asyncio.sleep(1)

    yield create_user_message("Now focus on the authentication module")

async def main():
    async for message in execute(generate_messages()):
        if message.type == "result":
            print(message.result)

asyncio.run(main())
```

### Settings File Configuration

Configure Amp's behavior with a settings file, like the `settings.json`. You can provide Amp with a custom settings file you have saved in your project:

```python
from amp_sdk import execute, AmpOptions

async def main():
    # Use a custom settings file
    async for message in execute(
        "Deploy the application",
        AmpOptions(
            settings_file="./settings.json",
            log_level="debug"
        )
    ):
        # Handle messages...
        pass

asyncio.run(main())
```

Example `settings.json`:

```json
{
	"amp.mcpServers": {
		"playwright": {
			"command": "npx",
			"args": ["-y", "@playwright/mcp@latest", "--headless", "--isolated"]
		}
	},
	"amp.commands.allowlist": ["npx", "node", "npm"],
	"amp.tools.disable": ["mermaid", "mcp__playwright__browser_resize"]
}
```

To find all available settings, see the [Configuration Settings](https://ampcode.com/manual#configuration).

### Custom Tools

Extend Amp's capabilities with custom toolbox scripts:

```python
from amp_sdk import execute, AmpOptions

async def main():
    async for message in execute(
        "Use my custom deployment scripts",
        AmpOptions(
            toolbox="/usr/repository-path/toolbox"  # Path to toolbox scripts
        )
    ):
        # Handle messages...
        pass

asyncio.run(main())
```

To find out more about Amp Toolboxes, see the [Toolboxes](https://ampcode.com/manual#toolboxes) section of the Amp documentation.

### Custom Skills

Load custom skills from a specified directory:

```python
from amp_sdk import execute, AmpOptions

async def main():
    async for message in execute(
        "Use my deployment skill",
        AmpOptions(
            skills="./my-skills"  # Path to custom skills directory
        )
    ):
        # Handle messages...
        pass

asyncio.run(main())
```

To learn more about creating custom skills, see the [Agent Skills](https://ampcode.com/manual#agent-skills) section of the Amp documentation.

## Functions

### execute()

The main function for executing Amp CLI commands programmatically.

```python
async def execute(
		prompt: Union[str, AsyncIterator[UserInputMessage]],
		options: Optional[AmpOptions] = None
) -> AsyncIterator[StreamMessage]
```

#### Parameters

- `prompt` (`str | AsyncIterator[UserInputMessage]`) - The user prompt as a string or async iterator of user input messages for multi-turn conversations
- `options` ([`AmpOptions`](#ampoptions), optional) - Configuration options for Amp execution

#### Returns

- `AsyncIterator[StreamMessage]` - Stream of messages from the Amp CLI

#### Example

```python
import asyncio
from amp_sdk import execute, AmpOptions

async def main():
		async for message in execute(
				"Analyze this codebase",
				AmpOptions(
						cwd="./my-project",
						dangerously_allow_all=True
				)
		):
				if message.type == "assistant":
						print("Assistant:", message.message.content)
				elif message.type == "result":
						print("Final result:", message.result)
						break

asyncio.run(main())
```

### create_user_message()

Helper function to create properly formatted user input messages for streaming conversations.

```python
def create_user_message(text: str) -> UserInputMessage
```

#### Parameters

- `text` (`str`) - The text content for the user message

#### Returns

- [`UserInputMessage`](#userinputmessage) - A formatted user input message

#### Example

```python
from amp_sdk import create_user_message

message = create_user_message("Analyze this code")
print(message)
# Output: UserInputMessage(type='user', message={'role': 'user', 'content': [{'type': 'text', 'text': 'Analyze this code'}]})
```

### create_permission()

Helper function to create permission objects for controlling tool usage.

```python
def create_permission(
		tool: str,
		action: Literal["allow", "reject", "ask", "delegate"],
		options: Optional[dict[str, Any]] = None
) -> Permission
```

#### Parameters

- `tool` (`str`) - The name of the tool to which this permission applies (supports glob patterns)
- `action` (`Literal["allow", "reject", "ask", "delegate"]`) - How Amp should proceed when matched
- `options` (`dict`, optional) - Additional configuration for the permission
  - `matches` (`dict[str, PermissionMatchCondition]`) - Match conditions for tool arguments
  - `context` (`Literal["thread", "subagent"]`) - Only apply this rule in specific context
  - `to` (`str`) - Command to delegate to (required when action is `"delegate"`)

#### Returns

- [`Permission`](#permission) - A permission object that can be used in the permissions list

#### Examples

```python
from amp_sdk import create_permission

# Allow all Bash commands
create_permission("Bash", "allow")

# Allow specific git commands
create_permission("Bash", "allow", {
		"matches": {"cmd": "git *"}
})

# Ask before allowing Read operations on sensitive paths
create_permission("Read", "ask", {
		"matches": {"path": "/etc/*"}
})

# Delegate web browsing to a custom command
create_permission("mcp__playwright__*", "delegate", {
		"to": "node browse.js"
})

# Only apply in subagent context
create_permission("Bash", "reject", {
		"context": "subagent"
})
```

## Types

### AmpOptions

Configuration options for the `execute()` function.

```python
class AmpOptions(BaseModel):
		cwd: Optional[str] = None
		mode: Literal["smart", "rush", "large"] = "smart"
		dangerously_allow_all: bool = False
		visibility: Optional[Literal["private", "public", "workspace", "group"]] = "workspace"
		settings_file: Optional[str] = None
		log_level: Optional[Literal["debug", "info", "warn", "error", "audit"]] = None
		log_file: Optional[str] = None
		env: dict[str, str] = Field(default_factory=dict)
		continue_thread: Union[bool, str, None] = None
		mcp_config: Optional[Union[MCPConfig, str]] = None
		toolbox: Optional[str] = None
		skills: Optional[str] = None
		permissions: Optional[list[Permission]] = None
```

#### Properties

| Property                | Type                                                         | Default       | Description                                                           |
| ----------------------- | ------------------------------------------------------------ | ------------- | --------------------------------------------------------------------- |
| `cwd`                   | `str \| None`                                                | `None`        | Current working directory for execution                               |
| `mode`                  | `Literal["smart", "rush", "large"]`                          | `"smart"`     | Agent mode - controls model, system prompt, and tool selection        |
| `dangerously_allow_all` | `bool`                                                       | `False`       | Allow all tool usage without permission prompts                       |
| `visibility`            | `Literal["public", "private", "workspace", "group"] \| None` | `"workspace"` | Thread visibility level                                               |
| `settings_file`         | `str \| None`                                                | `None`        | Path to custom settings file                                          |
| `log_level`             | `Literal["debug", "info", "warn", "error", "audit"] \| None` | `None`        | Logging verbosity level                                               |
| `log_file`              | `str \| None`                                                | `None`        | Path to write logs                                                    |
| `continue_thread`       | `bool \| str \| None`                                        | `None`        | Continue most recent thread (`True`) or specific thread by ID (`str`) |
| `mcp_config`            | `MCPConfig \| str \| None`                                   | `None`        | MCP server configuration as JSON string, dict, or config object       |
| `env`                   | `dict[str, str]`                                             | `{}`          | Additional environment variables                                      |
| `toolbox`               | `str \| None`                                                | `None`        | Folder path with toolbox scripts                                      |
| `skills`                | `str \| None`                                                | `None`        | Folder path with custom skills                                        |
| `permissions`           | `list[Permission] \| None`                                   | `None`        | Permission rules for tool usage                                       |

## Message Types

The SDK streams various message types during execution. All messages implement the base `StreamMessage` type.

### SystemMessage

Initial message containing session information and available tools.

```python
class SystemMessage(BaseModel):
		type: Literal["system"] = "system"
		subtype: Literal["init"] = "init"
		session_id: str
		cwd: str
		tools: list[str]
		mcp_servers: list[MCPServerStatus]
```

#### Properties

| Property      | Type                    | Description                                  |
| ------------- | ----------------------- | -------------------------------------------- |
| `session_id`  | `str`                   | Unique identifier for this execution session |
| `cwd`         | `str`                   | Current working directory                    |
| `tools`       | `list[str]`             | List of available tool names                 |
| `mcp_servers` | `list[MCPServerStatus]` | Status of MCP servers                        |

### AssistantMessage

AI assistant responses with text content and tool usage.

```python
class AssistantMessage(BaseModel):
		type: Literal["assistant"] = "assistant"
		session_id: str
		message: AssistantMessageDetails
		parent_tool_use_id: Optional[str] = None
```

#### Properties

| Property              | Type                                                    | Description                                      |
| --------------------- | ------------------------------------------------------- | ------------------------------------------------ |
| `session_id`          | `str`                                                   | Unique identifier for this execution session     |
| `message`             | `AssistantMessageDetails`                               | The assistant's message content                  |
| `message.id`          | `str \| None`                                           | Message identifier                               |
| `message.role`        | `Literal["assistant"]`                                  | Message role (always "assistant")                |
| `message.model`       | `str \| None`                                           | Model used to generate this response             |
| `message.content`     | `list[TextContent \| ToolUseContent]`                   | Message content blocks                           |
| `message.stop_reason` | `Literal["end_turn", "tool_use", "max_tokens"] \| None` | Why generation stopped                           |
| `message.usage`       | `Usage \| None`                                         | Token usage information                          |
| `parent_tool_use_id`  | `str \| None`                                           | ID of parent tool use if this is from a subagent |

### UserMessage

User input message (echoed back in stream).

```python
class UserMessage(BaseModel):
		type: Literal["user"] = "user"
		session_id: str
		message: UserMessageDetails
		parent_tool_use_id: Optional[str] = None
```

#### Properties

| Property             | Type                                     | Description                                      |
| -------------------- | ---------------------------------------- | ------------------------------------------------ |
| `session_id`         | `str`                                    | Unique identifier for this execution session     |
| `message`            | `UserMessageDetails`                     | The user's message content                       |
| `message.role`       | `Literal["user"]`                        | Message role (always "user")                     |
| `message.content`    | `list[TextContent \| ToolResultContent]` | Message content blocks                           |
| `parent_tool_use_id` | `str \| None`                            | ID of parent tool use if this is from a subagent |

### ResultMessage

Final successful execution result.

```python
class ResultMessage(BaseModel):
		type: Literal["result"] = "result"
		subtype: Literal["success"] = "success"
		session_id: str
		is_error: Literal[False] = False
		result: str
		duration_ms: int
		num_turns: int
		usage: Optional[Usage] = None
		permission_denials: Optional[list[str]] = None
```

#### Properties

| Property             | Type                        | Description                                  |
| -------------------- | --------------------------- | -------------------------------------------- |
| `session_id`         | `str`                       | Unique identifier for this execution session |
| `result`             | `str`                       | The final result from the assistant          |
| `duration_ms`        | `int`                       | Total execution time in milliseconds         |
| `num_turns`          | `int`                       | Number of conversation turns                 |
| `usage`              | [`Usage`](#usage) \| `None` | Token usage information                      |
| `permission_denials` | `list[str] \| None`         | List of permissions that were denied         |

### ErrorResultMessage

Final error result indicating execution failure.

```python
class ErrorResultMessage(BaseModel):
		type: Literal["result"] = "result"
		subtype: Literal["error_during_execution", "error_max_turns"] = "error_during_execution"
		session_id: str
		is_error: Literal[True] = True
		error: str
		duration_ms: int
		num_turns: int
		usage: Optional[Usage] = None
		permission_denials: Optional[list[str]] = None
```

#### Properties

| Property             | Type                        | Description                                  |
| -------------------- | --------------------------- | -------------------------------------------- |
| `session_id`         | `str`                       | Unique identifier for this execution session |
| `error`              | `str`                       | Error message describing what went wrong     |
| `duration_ms`        | `int`                       | Total execution time in milliseconds         |
| `num_turns`          | `int`                       | Number of conversation turns                 |
| `usage`              | [`Usage`](#usage) \| `None` | Token usage information                      |
| `permission_denials` | `list[str] \| None`         | List of permissions that were denied         |

### TextContent

Plain text content block.

```python
class TextContent(BaseModel):
		type: Literal["text"] = "text"
		text: str
```

### ToolUseContent

Tool execution request.

```python
class ToolUseContent(BaseModel):
		type: Literal["tool_use"] = "tool_use"
		id: str
		name: str
		input: dict[str, Any]
```

### ToolResultContent

Result from tool execution.

```python
class ToolResultContent(BaseModel):
		type: Literal["tool_result"] = "tool_result"
		tool_use_id: str
		content: str
		is_error: bool = False
```

### Usage

Token usage and billing information from API calls.

```python
class Usage(BaseModel):
		input_tokens: int = 0
		output_tokens: int = 0
		cache_creation_input_tokens: int = 0
		cache_read_input_tokens: int = 0
		service_tier: Optional[str] = None
```

#### Properties

| Property                      | Type          | Description                        |
| ----------------------------- | ------------- | ---------------------------------- |
| `input_tokens`                | `int`         | Number of input tokens used        |
| `cache_creation_input_tokens` | `int`         | Tokens used for cache creation     |
| `cache_read_input_tokens`     | `int`         | Tokens read from cache             |
| `output_tokens`               | `int`         | Number of output tokens generated  |
| `service_tier`                | `str \| None` | Service tier used for this request |

## Input Types

### UserInputMessage

Formatted user input message for streaming conversations.

```python
class UserInputMessage(BaseModel):
		type: Literal["user"] = "user"
		message: UserInputMessageDetails
```

Where `UserInputMessageDetails` is:

```python
class UserInputMessageDetails(BaseModel):
		role: Literal["user"] = "user"
		content: list[Union[TextContent, ToolResultContent]]
```

### MCPConfig

Configuration for MCP (Model Context Protocol) servers.

```python
class MCPConfig(BaseModel):
		servers: dict[str, MCPServer] = Field(default_factory=dict)

		def to_json_string(self) -> str:
				"""Convert to JSON string for CLI argument."""
				...
```

### MCPServer

Individual MCP server configuration.

```python
class MCPServer(BaseModel):
		command: str
		args: list[str] = Field(default_factory=list)
		env: dict[str, str] = Field(default_factory=dict)
		disabled: Optional[bool] = False
```

#### Properties

| Property   | Type             | Required | Description                          |
| ---------- | ---------------- | -------- | ------------------------------------ |
| `command`  | `str`            | Yes      | Command to start the MCP server      |
| `args`     | `list[str]`      | No       | Command line arguments               |
| `env`      | `dict[str, str]` | No       | Environment variables for the server |
| `disabled` | `bool \| None`   | No       | Whether this server is disabled      |

### Permission

Individual permission rule for controlling tool usage.

```python
class Permission(BaseModel):
		tool: str
		matches: Optional[dict[str, Any]] = None
		action: Literal["allow", "reject", "ask", "delegate"]
		context: Optional[Literal["thread", "subagent"]] = None
		to: Optional[str] = None
```

#### Properties

| Property  | Type                                            | Required | Description                                                   |
| --------- | ----------------------------------------------- | -------- | ------------------------------------------------------------- |
| `tool`    | `str`                                           | Yes      | Tool name (supports glob patterns like `Bash` or `mcp__*`)    |
| `matches` | `dict[str, PermissionMatchCondition] \| None`   | No       | Match conditions for tool arguments                           |
| `action`  | `Literal["allow", "reject", "ask", "delegate"]` | Yes      | How Amp should proceed when the rule matches                  |
| `context` | `Literal["thread", "subagent"] \| None`         | No       | Apply rule only in main thread or sub-agents                  |
| `to`      | `str \| None`                                   | No       | Command to delegate to (required when action is `"delegate"`) |

#### Example

```python
from amp_sdk import execute, AmpOptions, create_permission

async def main():
		async for message in execute(
				"Deploy the application",
				AmpOptions(
						permissions=[
								# Allow git commands
								create_permission("Bash", "allow", {"matches": {"cmd": "git *"}}),
								# Allow reading files
								create_permission("Read", "allow"),
						]
				)
		):
				# Handle messages
				pass

asyncio.run(main())
```

### PermissionMatchCondition

Match condition for tool arguments. Supports strings (with glob patterns or regex), lists (OR logic), booleans, numbers, None, and nested dicts.

```python
PermissionMatchCondition = Union[
		str,
		bool,
		int,
		float,
		None,
		list['PermissionMatchCondition'],
		dict[str, 'PermissionMatchCondition']
]
```

#### Examples

```python
# String pattern with wildcard
{"cmd": "npm *"}

# List for OR logic
{"cmd": ["npm install", "npm test", "npm run build"]}

# Regex pattern
{"cmd": "/^git (status|log|diff)$/"}

# Nested dict matching
{"env": {"NODE_ENV": "production"}}
```

## Exceptions

The SDK provides several exception types for error handling:

### AmpError

Base exception for all Amp SDK errors.

```python
class AmpError(Exception):
		"""Base exception for Amp SDK errors."""
		pass
```

### CLINotFoundError

Raised when the Amp CLI cannot be found.

```python
class CLINotFoundError(AmpError):
		"""Amp CLI not found."""
		pass
```

### ProcessError

Raised when the CLI process fails.

```python
class ProcessError(AmpError):
		"""CLI process error."""
		exit_code: int
		stderr: str
		signal: Optional[str] = None
```

### ValidationError

Raised when input validation fails.

```python
class ValidationError(AmpError):
		"""Input validation error."""
		pass
```

### JSONParseError

Raised when JSON parsing fails.

```python
class JSONParseError(AmpError):
		"""JSON parsing error."""
		raw_line: str
```

### AmpTimeoutError

Raised when an operation times out.

```python
class AmpTimeoutError(AmpError):
		"""Operation timeout error."""
		pass
```

### CancellationError

Raised when an operation is cancelled.

```python
class CancellationError(AmpError):
		"""Operation cancelled."""
		pass
```

## Requirements

- Python 3.9 or higher
- The Amp CLI must be installed (`npm install -g @sourcegraph/amp`)
