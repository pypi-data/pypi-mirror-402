"""Tests for MCP (Model Context Protocol) client module."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from uma_api.mcp import (
    MCPContent,
    MCPError,
    MCPPrompt,
    MCPPromptMessage,
    MCPResource,
    MCPResourceContent,
    MCPTool,
    MCPToolResult,
    UnraidMCPClient,
)


def create_mock_response(json_data: dict[str, Any]) -> MagicMock:
    """Create a mock response that works as an async context manager."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=json_data)
    return mock_response


@asynccontextmanager
async def mock_post_context(response: MagicMock):
    """Async context manager for mocking session.post."""
    yield response


class TestMCPModels:
    """Test MCP Pydantic models."""

    def test_mcp_tool_model(self) -> None:
        """Test MCPTool model."""
        tool = MCPTool(
            name="get_system_info",
            description="Get system information",
            input_schema={"type": "object", "properties": {}},
        )
        assert tool.name == "get_system_info"
        assert tool.description == "Get system information"
        assert tool.input_schema == {"type": "object", "properties": {}}

    def test_mcp_resource_model(self) -> None:
        """Test MCPResource model."""
        resource = MCPResource(
            uri="unraid://system",
            name="system-info",
            description="Real-time Unraid system information",
            mime_type="application/json",
        )
        assert resource.uri == "unraid://system"
        assert resource.name == "system-info"
        assert resource.mime_type == "application/json"

    def test_mcp_prompt_model(self) -> None:
        """Test MCPPrompt model."""
        prompt = MCPPrompt(
            name="system_overview",
            description="Get a comprehensive overview of the system",
        )
        assert prompt.name == "system_overview"
        assert prompt.description == "Get a comprehensive overview of the system"

    def test_mcp_content_model(self) -> None:
        """Test MCPContent model."""
        content = MCPContent(type="text", text='{"hostname": "Cube"}')
        assert content.type == "text"
        assert content.text == '{"hostname": "Cube"}'

    def test_mcp_tool_result_model(self) -> None:
        """Test MCPToolResult model."""
        result = MCPToolResult(
            content=[MCPContent(type="text", text='{"hostname": "Cube"}')],
            is_error=False,
        )
        assert len(result.content) == 1
        assert result.is_error is False

    def test_mcp_resource_content_model(self) -> None:
        """Test MCPResourceContent model."""
        content = MCPResourceContent(
            uri="unraid://system",
            mime_type="application/json",
            text='{"hostname": "Cube"}',
        )
        assert content.uri == "unraid://system"
        assert content.mime_type == "application/json"

    def test_mcp_prompt_message_model(self) -> None:
        """Test MCPPromptMessage model."""
        message = MCPPromptMessage(
            role="user",
            content=MCPContent(type="text", text="Please analyze the system"),
        )
        assert message.role == "user"
        assert message.content.text == "Please analyze the system"


class TestUnraidMCPClientInit:
    """Test UnraidMCPClient initialization."""

    def test_basic_initialization(self) -> None:
        """Test basic client initialization."""
        client = UnraidMCPClient("192.168.1.100")
        assert client.host == "192.168.1.100"
        assert client.port == 8043
        assert client.base_url == "http://192.168.1.100:8043/mcp"
        assert client.timeout == 30

    def test_custom_port(self) -> None:
        """Test client with custom port."""
        client = UnraidMCPClient("192.168.1.100", port=9000)
        assert client.port == 9000
        assert client.base_url == "http://192.168.1.100:9000/mcp"

    def test_https_initialization(self) -> None:
        """Test client with HTTPS."""
        client = UnraidMCPClient("192.168.1.100", use_https=True)
        assert client.base_url == "https://192.168.1.100:8043/mcp"

    def test_custom_timeout(self) -> None:
        """Test client with custom timeout."""
        client = UnraidMCPClient("192.168.1.100", timeout=60)
        assert client.timeout == 60


class TestUnraidMCPClientContextManager:
    """Test UnraidMCPClient async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test async context manager creates and closes session."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            async with UnraidMCPClient("192.168.1.100") as client:
                assert client._session is not None

            mock_session.close.assert_called_once()


class TestUnraidMCPClientRPC:
    """Test UnraidMCPClient JSON-RPC methods."""

    @pytest.fixture
    def client(self) -> UnraidMCPClient:
        """Create a test client."""
        return UnraidMCPClient("192.168.1.100")

    def _setup_mock_session(self, client: UnraidMCPClient, json_data: dict[str, Any]) -> MagicMock:
        """Set up mock session with proper async context manager."""
        mock_response = create_mock_response(json_data)
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_post_context(mock_response))
        client._session = mock_session
        return mock_session

    @pytest.mark.asyncio
    async def test_list_tools(self, client: UnraidMCPClient) -> None:
        """Test list_tools method."""
        self._setup_mock_session(
            client,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "tools": [
                        {
                            "name": "get_system_info",
                            "description": "Get system information",
                            "inputSchema": {"type": "object"},
                        },
                        {
                            "name": "list_containers",
                            "description": "List Docker containers",
                            "inputSchema": {"type": "object"},
                        },
                    ]
                },
            },
        )

        tools = await client.list_tools()

        assert len(tools) == 2
        assert tools[0].name == "get_system_info"
        assert tools[1].name == "list_containers"

    @pytest.mark.asyncio
    async def test_call_tool(self, client: UnraidMCPClient) -> None:
        """Test call_tool method."""
        self._setup_mock_session(
            client,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "content": [{"type": "text", "text": '{"hostname": "Cube"}'}],
                    "isError": False,
                },
            },
        )

        result = await client.call_tool("get_system_info", {})

        assert result.is_error is False
        assert len(result.content) == 1
        assert '{"hostname": "Cube"}' in result.content[0].text

    @pytest.mark.asyncio
    async def test_call_tool_with_arguments(self, client: UnraidMCPClient) -> None:
        """Test call_tool with arguments."""
        mock_session = self._setup_mock_session(
            client,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "content": [{"type": "text", "text": "Container started"}],
                    "isError": False,
                },
            },
        )

        result = await client.call_tool(
            "container_action", {"container_id": "plex", "action": "start"}
        )

        assert result.is_error is False

        # Verify the request was made with correct arguments
        call_args = mock_session.post.call_args
        json_data = call_args[1]["json"]
        assert json_data["params"]["name"] == "container_action"
        assert json_data["params"]["arguments"]["container_id"] == "plex"
        assert json_data["params"]["arguments"]["action"] == "start"

    @pytest.mark.asyncio
    async def test_list_resources(self, client: UnraidMCPClient) -> None:
        """Test list_resources method."""
        self._setup_mock_session(
            client,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "resources": [
                        {
                            "uri": "unraid://system",
                            "name": "system-info",
                            "description": "Real-time system info",
                            "mimeType": "application/json",
                        },
                        {
                            "uri": "unraid://array",
                            "name": "array-status",
                            "description": "Real-time array status",
                            "mimeType": "application/json",
                        },
                    ]
                },
            },
        )

        resources = await client.list_resources()

        assert len(resources) == 2
        assert resources[0].uri == "unraid://system"
        assert resources[1].uri == "unraid://array"

    @pytest.mark.asyncio
    async def test_read_resource(self, client: UnraidMCPClient) -> None:
        """Test read_resource method."""
        self._setup_mock_session(
            client,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "contents": [
                        {
                            "uri": "unraid://system",
                            "mimeType": "application/json",
                            "text": '{"hostname": "Cube"}',
                        }
                    ]
                },
            },
        )

        contents = await client.read_resource("unraid://system")

        assert len(contents) == 1
        assert contents[0].uri == "unraid://system"
        assert '{"hostname": "Cube"}' in contents[0].text

    @pytest.mark.asyncio
    async def test_list_prompts(self, client: UnraidMCPClient) -> None:
        """Test list_prompts method."""
        self._setup_mock_session(
            client,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "prompts": [
                        {
                            "name": "system_overview",
                            "description": "Get system overview",
                        },
                        {
                            "name": "analyze_disk_health",
                            "description": "Analyze disk health",
                        },
                    ]
                },
            },
        )

        prompts = await client.list_prompts()

        assert len(prompts) == 2
        assert prompts[0].name == "system_overview"
        assert prompts[1].name == "analyze_disk_health"

    @pytest.mark.asyncio
    async def test_get_prompt(self, client: UnraidMCPClient) -> None:
        """Test get_prompt method."""
        self._setup_mock_session(
            client,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "description": "System overview",
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": "Please analyze the system...",
                            },
                        }
                    ],
                },
            },
        )

        messages = await client.get_prompt("system_overview")

        assert len(messages) == 1
        assert messages[0].role == "user"
        assert "analyze the system" in messages[0].content.text


class TestUnraidMCPClientErrors:
    """Test UnraidMCPClient error handling."""

    @pytest.fixture
    def client(self) -> UnraidMCPClient:
        """Create a test client."""
        return UnraidMCPClient("192.168.1.100")

    def _setup_mock_session(self, client: UnraidMCPClient, json_data: dict[str, Any]) -> MagicMock:
        """Set up mock session with proper async context manager."""
        mock_response = create_mock_response(json_data)
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_post_context(mock_response))
        client._session = mock_session
        return mock_session

    @pytest.mark.asyncio
    async def test_rpc_error(self, client: UnraidMCPClient) -> None:
        """Test JSON-RPC error handling."""
        self._setup_mock_session(
            client,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {"code": -32600, "message": "Invalid Request"},
            },
        )

        with pytest.raises(MCPError) as exc_info:
            await client.list_tools()

        assert exc_info.value.code == -32600
        assert "Invalid Request" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_tool_not_found_error(self, client: UnraidMCPClient) -> None:
        """Test tool not found error."""
        self._setup_mock_session(
            client,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {"code": -32601, "message": "Tool not found: invalid_tool"},
            },
        )

        with pytest.raises(MCPError) as exc_info:
            await client.call_tool("invalid_tool", {})

        assert "Tool not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_connection_error(self, client: UnraidMCPClient) -> None:
        """Test connection error handling."""
        import aiohttp

        mock_session = MagicMock()

        @asynccontextmanager
        async def raise_error():
            raise aiohttp.ClientError("Connection refused")
            yield  # noqa: B901 - unreachable, but needed for syntax

        mock_session.post = MagicMock(return_value=raise_error())
        client._session = mock_session

        with pytest.raises(MCPError) as exc_info:
            await client.list_tools()

        assert "Connection" in str(exc_info.value)


class TestUnraidMCPClientConvenience:
    """Test UnraidMCPClient convenience methods."""

    @pytest.fixture
    def client(self) -> UnraidMCPClient:
        """Create a test client."""
        return UnraidMCPClient("192.168.1.100")

    def _setup_mock_session(self, client: UnraidMCPClient, json_data: dict[str, Any]) -> MagicMock:
        """Set up mock session with proper async context manager."""
        mock_response = create_mock_response(json_data)
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_post_context(mock_response))
        client._session = mock_session
        return mock_session

    @pytest.mark.asyncio
    async def test_get_system_info(self, client: UnraidMCPClient) -> None:
        """Test get_system_info convenience method."""
        self._setup_mock_session(
            client,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": '{"hostname": "Cube", "version": "7.2.3"}',
                        }
                    ],
                    "isError": False,
                },
            },
        )

        result = await client.get_system_info()

        assert result["hostname"] == "Cube"
        assert result["version"] == "7.2.3"

    @pytest.mark.asyncio
    async def test_get_array_status(self, client: UnraidMCPClient) -> None:
        """Test get_array_status convenience method."""
        self._setup_mock_session(
            client,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": '{"state": "STARTED", "parity_valid": true}',
                        }
                    ],
                    "isError": False,
                },
            },
        )

        result = await client.get_array_status()

        assert result["state"] == "STARTED"
        assert result["parity_valid"] is True

    @pytest.mark.asyncio
    async def test_list_containers(self, client: UnraidMCPClient) -> None:
        """Test list_containers convenience method."""
        self._setup_mock_session(
            client,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": '[{"name": "plex", "state": "running"}]',
                        }
                    ],
                    "isError": False,
                },
            },
        )

        result = await client.list_containers()

        assert len(result) == 1
        assert result[0]["name"] == "plex"

    @pytest.mark.asyncio
    async def test_container_action(self, client: UnraidMCPClient) -> None:
        """Test container_action convenience method."""
        self._setup_mock_session(
            client,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "content": [{"type": "text", "text": "Container started"}],
                    "isError": False,
                },
            },
        )

        result = await client.container_action("plex", "start")

        assert result.is_error is False
        assert "started" in result.content[0].text
