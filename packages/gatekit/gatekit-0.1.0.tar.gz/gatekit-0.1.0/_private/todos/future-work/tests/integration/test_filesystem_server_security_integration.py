"""Integration test for FilesystemServerSecurityPlugin to verify plugin loading and basic functionality."""

import pytest
from gatekit.plugins.manager import PluginManager
from gatekit.protocol.messages import MCPRequest
from gatekit.plugins.interfaces import PipelineOutcome


@pytest.mark.asyncio
async def test_plugin_discovery_and_loading():
    """Test that the filesystem server security plugin can be discovered and loaded."""
    config = {
        "security": {
            "_global": [
                {
                    "handler": "filesystem_server",
                    "config": {
                        "enabled": True,
                        "critical": False,  # Non-critical for testing with non-existent paths
                        "read": ["docs/*", "public/**/*.txt"],
                        "write": ["uploads/*", "admin/**/*"],
                    },
                }
            ]
        },
        "auditing": {"_global": []},
    }

    plugin_manager = PluginManager(config)
    await plugin_manager.load_plugins()

    # Verify plugin was loaded
    assert len(plugin_manager.security_plugins) == 1
    assert (
        plugin_manager.security_plugins[0].__class__.__name__
        == "FilesystemServerSecurityPlugin"
    )


@pytest.mark.asyncio
async def test_end_to_end_request_processing():
    """Test end-to-end request processing through the plugin manager."""
    config = {
        "security": {
            "_global": [
                {
                    "handler": "filesystem_server",
                    "config": {
                        "enabled": True,
                        "critical": False,  # Non-critical for testing with non-existent paths
                        "read": ["docs/*"],
                        "write": ["uploads/*"],
                    },
                }
            ]
        },
        "auditing": {"_global": []},
    }

    plugin_manager = PluginManager(config)
    await plugin_manager.load_plugins()

    # Test allowed read request
    allowed_request = MCPRequest(
        jsonrpc="2.0",
        method="tools/call",
        params={"name": "read_file", "arguments": {"path": "docs/readme.md"}},
        id="test-1",
    )

    pipeline_allowed = await plugin_manager.process_request(allowed_request)
    assert pipeline_allowed.pipeline_outcome == PipelineOutcome.ALLOWED

    # Test denied read request
    denied_request = MCPRequest(
        jsonrpc="2.0",
        method="tools/call",
        params={"name": "read_file", "arguments": {"path": "secret/config.txt"}},
        id="test-2",
    )

    pipeline_denied = await plugin_manager.process_request(denied_request)
    assert pipeline_denied.pipeline_outcome == PipelineOutcome.BLOCKED
    # Extract blocking stage and assert its outcome; reason may be sanitized to "[blocked]" when capture_content=False
    blocking_stage = next(
        (s for s in pipeline_denied.stages if s.outcome.value == "blocked"), None
    )
    assert blocking_stage is not None
    assert blocking_stage.outcome.value == "blocked"


@pytest.mark.asyncio
async def test_plugin_with_empty_config():
    """Test plugin behavior with empty configuration (should deny all)."""
    config = {
        "security": {
            "_global": [
                {
                    "handler": "filesystem_server",
                    "enabled": True,
                    "critical": False,  # Non-critical for testing
                    "config": {},
                }
            ]
        },
        "auditing": {"_global": []},
    }

    plugin_manager = PluginManager(config)
    await plugin_manager.load_plugins()

    # Test that empty config denies filesystem requests
    request = MCPRequest(
        jsonrpc="2.0",
        method="tools/call",
        params={"name": "read_file", "arguments": {"path": "any/file.txt"}},
        id="test-3",
    )

    pipeline_empty = await plugin_manager.process_request(request)
    assert pipeline_empty.pipeline_outcome == PipelineOutcome.BLOCKED
