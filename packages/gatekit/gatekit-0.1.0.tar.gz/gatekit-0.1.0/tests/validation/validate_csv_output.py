"""Validation tests for CSV formatter using external tools.

These tests use optional dependencies that are only available in test environments.
They validate CSV format compliance with external tools like pandas.
"""

import pytest
import tempfile
import os
from gatekit.plugins.auditing.csv import CsvAuditingPlugin
from gatekit.plugins.interfaces import (
    PluginResult,
    ProcessingPipeline,
    PipelineOutcome,
    PipelineStage,
    StageOutcome,
)
from gatekit.protocol.messages import MCPRequest, MCPResponse


class TestCSVValidationWithPandas:
    """Test CSV format validation with pandas DataFrame."""

    def test_csv_with_pandas_basic(self):
        """Test CSV format with pandas DataFrame parsing."""
        pd = pytest.importorskip("pandas")

        # Create CSV plugin
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.csv")
            config = {"output_file": log_file, "format": "csv", "critical": False}
            plugin = CsvAuditingPlugin(config)

            # Create sample events with proper ProcessingPipeline objects
            events = []

            # Event 1: Allowed request
            req1 = MCPRequest(
                jsonrpc="2.0",
                id="req-1",
                method="tools/call",
                params={"name": "read_file"},
            )
            pipeline1 = ProcessingPipeline(
                original_content=req1,
                pipeline_outcome=PipelineOutcome.ALLOWED,
                had_security_plugin=True,
            )
            pipeline1.add_stage(
                PipelineStage(
                    plugin_name="test",
                    plugin_type="security",
                    input_content=req1,
                    output_content=req1,
                    content_hash="hash1",
                    result=PluginResult(
                        allowed=True, reason="Allowed", metadata={"plugin": "test"}
                    ),
                    processing_time_ms=1.0,
                    outcome=StageOutcome.ALLOWED,
                    security_evaluated=True,
                )
            )
            events.append((req1, pipeline1))

            # Event 2: Blocked request
            req2 = MCPRequest(
                jsonrpc="2.0",
                id="req-2",
                method="tools/call",
                params={"name": "write_file"},
            )
            pipeline2 = ProcessingPipeline(
                original_content=req2,
                pipeline_outcome=PipelineOutcome.BLOCKED,
                had_security_plugin=True,
            )
            pipeline2.add_stage(
                PipelineStage(
                    plugin_name="test",
                    plugin_type="security",
                    input_content=req2,
                    output_content=req2,
                    content_hash="hash2",
                    result=PluginResult(
                        allowed=False, reason="Blocked", metadata={"plugin": "test"}
                    ),
                    processing_time_ms=1.0,
                    outcome=StageOutcome.BLOCKED,
                    security_evaluated=True,
                )
            )
            events.append((req2, pipeline2))

            # Event 3: Allowed resources request
            req3 = MCPRequest(
                jsonrpc="2.0", id="req-3", method="resources/list", params={}
            )
            pipeline3 = ProcessingPipeline(
                original_content=req3,
                pipeline_outcome=PipelineOutcome.ALLOWED,
                had_security_plugin=True,
            )
            pipeline3.add_stage(
                PipelineStage(
                    plugin_name="test",
                    plugin_type="security",
                    input_content=req3,
                    output_content=req3,
                    content_hash="hash3",
                    result=PluginResult(
                        allowed=True, reason="Allowed", metadata={"plugin": "test"}
                    ),
                    processing_time_ms=1.0,
                    outcome=StageOutcome.ALLOWED,
                    security_evaluated=True,
                )
            )
            events.append((req3, pipeline3))

            # Log all events
            import asyncio

            async def log_events():
                for request, pipeline in events:
                    await plugin.log_request(request, pipeline, "test-server")

            asyncio.run(log_events())

            # Parse with pandas
            df = pd.read_csv(log_file)

            # Verify structure
            assert len(df) == 3
            expected_columns = [
                "timestamp",
                "event_type",
                "request_id",
                "server_name",
                "method",
                "tool",
                "pipeline_outcome",
                "security_evaluated",
                "decision_plugin",
                "decision_type",
                "total_plugins_run",
                "plugins_run",
                "reason",
                "duration_ms",
                "response_type",
                "error_code",
                "error_message",
                "error_classification",
            ]
            assert list(df.columns) == expected_columns

            # Verify data types and content
            assert df["event_type"].notna().all()
            assert df["timestamp"].notna().all()
            assert df["request_id"].notna().all()

            # Verify specific values
            assert df.iloc[0]["event_type"] == "REQUEST"
            assert df.iloc[0]["method"] == "tools/call"
            assert df.iloc[0]["tool"] == "read_file"
            assert df.iloc[0]["pipeline_outcome"] == "allowed"

            assert df.iloc[1]["event_type"] == "SECURITY_BLOCK"
            assert df.iloc[1]["pipeline_outcome"] == "blocked"

            assert df.iloc[2]["event_type"] == "REQUEST"
            assert df.iloc[2]["method"] == "resources/list"
            assert pd.isna(
                df.iloc[2]["tool"]
            )  # Empty for non-tools/call (pandas reads as NaN)

    def test_csv_with_pandas_complex_data(self):
        """Test CSV format with complex data structures."""
        pd = pytest.importorskip("pandas")

        # Create CSV plugin
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.csv")
            config = {"output_file": log_file, "format": "csv", "critical": False}
            plugin = CsvAuditingPlugin(config)

            # Create request with complex data
            request = MCPRequest(
                jsonrpc="2.0",
                id="req-complex",
                method="tools/call",
                params={
                    "name": "complex_tool",
                    "arguments": {
                        "nested": {"key": "value"},
                        "list": [1, 2, 3],
                        "string": 'test with, comma and "quotes"',
                    },
                },
            )

            # Create ProcessingPipeline with proper structure
            pipeline = ProcessingPipeline(
                original_content=request,
                pipeline_outcome=PipelineOutcome.ALLOWED,
                had_security_plugin=True,
            )
            pipeline.add_stage(
                PipelineStage(
                    plugin_name="complex_plugin",
                    plugin_type="security",
                    input_content=request,
                    output_content=request,
                    content_hash="complex_hash",
                    result=PluginResult(
                        allowed=True,
                        reason="Request with complex data approved",
                        metadata={"plugin": "complex_plugin", "mode": "test"},
                    ),
                    processing_time_ms=1.0,
                    outcome=StageOutcome.ALLOWED,
                    security_evaluated=True,
                )
            )

            # Log event
            import asyncio

            async def log_event():
                await plugin.log_request(request, pipeline, "test-server")

            asyncio.run(log_event())

            # Parse with pandas
            df = pd.read_csv(log_file)

            # Verify structure
            assert len(df) == 1

            # Verify complex data handling
            row = df.iloc[0]
            assert row["event_type"] == "REQUEST"
            assert row["method"] == "tools/call"
            assert row["tool"] == "complex_tool"
            assert row["pipeline_outcome"] == "allowed"
            assert (
                row["reason"] == "[complex_plugin] Request with complex data approved"
            )
            assert row["decision_plugin"] == "complex_plugin"

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    def test_csv_with_pandas_data_types(self):
        """Test CSV format data type handling with pandas."""
        pd = pytest.importorskip("pandas")

        # Create CSV plugin
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.csv")
            config = {"output_file": log_file, "format": "csv", "critical": False}
            plugin = CsvAuditingPlugin(config)

            # Create response with duration
            request = MCPRequest(jsonrpc="2.0", id="req-duration", method="tools/call")
            response = MCPResponse(
                jsonrpc="2.0", id="req-duration", result={"status": "ok"}
            )

            # Create ProcessingPipeline
            pipeline = ProcessingPipeline(
                original_content=response,
                pipeline_outcome=PipelineOutcome.ALLOWED,
                had_security_plugin=True,
            )
            pipeline.add_stage(
                PipelineStage(
                    plugin_name="test_plugin",
                    plugin_type="security",
                    input_content=response,
                    output_content=response,
                    content_hash="response_hash",
                    result=PluginResult(
                        allowed=True,
                        reason="Response approved",
                        metadata={"plugin": "test_plugin", "duration_ms": 150},
                    ),
                    processing_time_ms=150.0,
                    outcome=StageOutcome.ALLOWED,
                    security_evaluated=True,
                )
            )

            # Log event
            import asyncio

            async def log_event():
                await plugin.log_response(request, response, pipeline, "test-server")

            asyncio.run(log_event())

            # Parse with pandas
            df = pd.read_csv(log_file)

            # Verify data types
            assert len(df) == 1
            row = df.iloc[0]

            # Duration should be readable as integer
            assert pd.notna(row["duration_ms"])
            assert row["duration_ms"] == 150  # pandas auto-converts to int64

            # Should be convertible to numeric
            df["duration_ms"] = pd.to_numeric(df["duration_ms"], errors="coerce")
            assert df.iloc[0]["duration_ms"] == 150

    def test_csv_with_pandas_special_characters(self):
        """Test CSV format with special characters using pandas."""
        pd = pytest.importorskip("pandas")

        # Create CSV plugin
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.csv")
            config = {"output_file": log_file, "format": "csv", "critical": False}
            plugin = CsvAuditingPlugin(config)

            # Create request with special characters
            special_reason = 'Contains "quotes", newlines\nand commas, and more'
            request = MCPRequest(
                jsonrpc="2.0",
                id="req-special",
                method="tools/call",
                params={"name": "special_tool"},
            )

            # Create ProcessingPipeline
            pipeline = ProcessingPipeline(
                original_content=request,
                pipeline_outcome=PipelineOutcome.BLOCKED,
                had_security_plugin=True,
            )
            pipeline.add_stage(
                PipelineStage(
                    plugin_name="special_plugin",
                    plugin_type="security",
                    input_content=request,
                    output_content=request,
                    content_hash="special_hash",
                    result=PluginResult(
                        allowed=False,
                        reason=special_reason,
                        metadata={"plugin": "special_plugin"},
                    ),
                    processing_time_ms=1.0,
                    outcome=StageOutcome.BLOCKED,
                    security_evaluated=True,
                )
            )

            # Log event
            import asyncio

            async def log_event():
                await plugin.log_request(request, pipeline, "test-server")

            asyncio.run(log_event())

            # Parse with pandas
            df = pd.read_csv(log_file)

            # Verify special characters are preserved
            assert len(df) == 1
            row = df.iloc[0]
            assert row["reason"] == f"[special_plugin] {special_reason}"
            assert row["event_type"] == "SECURITY_BLOCK"
            assert row["tool"] == "special_tool"


class TestCSVValidationWithBuiltinCSV:
    """Test CSV format validation with Python's built-in csv module."""

    def test_csv_with_builtin_csv_reader(self):
        """Test CSV format with Python's csv.reader."""
        import csv

        # Create CSV plugin
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.csv")
            config = {"output_file": log_file, "format": "csv", "critical": False}
            plugin = CsvAuditingPlugin(config)

            # Create and log events
            events = []

            # Event 1
            req1 = MCPRequest(
                jsonrpc="2.0",
                id="req-1",
                method="tools/call",
                params={"name": "read_file"},
            )
            pipeline1 = ProcessingPipeline(
                original_content=req1,
                pipeline_outcome=PipelineOutcome.ALLOWED,
                had_security_plugin=True,
            )
            pipeline1.add_stage(
                PipelineStage(
                    plugin_name="test",
                    plugin_type="security",
                    input_content=req1,
                    output_content=req1,
                    content_hash="hash1",
                    result=PluginResult(
                        allowed=True, reason="Allowed", metadata={"plugin": "test"}
                    ),
                    processing_time_ms=1.0,
                    outcome=StageOutcome.ALLOWED,
                    security_evaluated=True,
                )
            )
            events.append((req1, pipeline1))

            # Event 2
            req2 = MCPRequest(
                jsonrpc="2.0",
                id="req-2",
                method="tools/call",
                params={"name": "write_file"},
            )
            pipeline2 = ProcessingPipeline(
                original_content=req2,
                pipeline_outcome=PipelineOutcome.BLOCKED,
                had_security_plugin=True,
            )
            pipeline2.add_stage(
                PipelineStage(
                    plugin_name="test",
                    plugin_type="security",
                    input_content=req2,
                    output_content=req2,
                    content_hash="hash2",
                    result=PluginResult(
                        allowed=False, reason="Blocked", metadata={"plugin": "test"}
                    ),
                    processing_time_ms=1.0,
                    outcome=StageOutcome.BLOCKED,
                    security_evaluated=True,
                )
            )
            events.append((req2, pipeline2))

            import asyncio

            async def log_events():
                for request, pipeline in events:
                    await plugin.log_request(request, pipeline, "test-server")

            asyncio.run(log_events())

            # Parse with csv.reader
            with open(log_file, "r") as f:
                reader = csv.reader(f)
                rows = list(reader)

            # Verify structure
            assert len(rows) == 3  # Header + 2 data rows

            # Verify header
            expected_header = [
                "timestamp",
                "event_type",
                "request_id",
                "server_name",
                "method",
                "tool",
                "pipeline_outcome",
                "security_evaluated",
                "decision_plugin",
                "decision_type",
                "total_plugins_run",
                "plugins_run",
                "reason",
                "duration_ms",
                "response_type",
                "error_code",
                "error_message",
                "error_classification",
            ]
            assert rows[0] == expected_header

            # Verify data rows (new column order)
            assert rows[1][1] == "REQUEST"  # event_type
            assert rows[1][4] == "tools/call"  # method
            assert rows[1][5] == "read_file"  # tool
            assert rows[1][6] == "allowed"  # pipeline_outcome

            assert rows[2][1] == "SECURITY_BLOCK"  # event_type
            assert rows[2][6] == "blocked"  # pipeline_outcome

    def test_csv_with_builtin_csv_dictreader(self):
        """Test CSV format with Python's csv.DictReader."""
        import csv

        # Create CSV plugin
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.csv")
            config = {"output_file": log_file, "format": "csv", "critical": False}
            plugin = CsvAuditingPlugin(config)

            # Create and log a complex event
            request = MCPRequest(
                jsonrpc="2.0",
                id="req-dict-test",
                method="tools/call",
                params={"name": "test_tool"},
            )

            # Create ProcessingPipeline
            pipeline = ProcessingPipeline(
                original_content=request,
                pipeline_outcome=PipelineOutcome.ALLOWED,
                had_security_plugin=True,
            )
            pipeline.add_stage(
                PipelineStage(
                    plugin_name="dict_test_plugin",
                    plugin_type="security",
                    input_content=request,
                    output_content=request,
                    content_hash="dict_hash",
                    result=PluginResult(
                        allowed=True,
                        reason='Test with special chars: ", \n, ,',
                        metadata={"plugin": "dict_test_plugin", "mode": "test"},
                    ),
                    processing_time_ms=1.0,
                    outcome=StageOutcome.ALLOWED,
                    security_evaluated=True,
                )
            )

            import asyncio

            async def log_event():
                await plugin.log_request(request, pipeline, "test-server")

            asyncio.run(log_event())

            # Parse with csv.DictReader
            with open(log_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            # Verify structure
            assert len(rows) == 1
            row = rows[0]

            # Verify all expected fields are present
            expected_fields = [
                "timestamp",
                "event_type",
                "request_id",
                "server_name",
                "method",
                "tool",
                "pipeline_outcome",
                "security_evaluated",
                "decision_plugin",
                "decision_type",
                "total_plugins_run",
                "plugins_run",
                "reason",
                "duration_ms",
            ]
            for field in expected_fields:
                assert field in row

            # Verify data
            assert row["event_type"] == "REQUEST"
            assert row["method"] == "tools/call"
            assert row["tool"] == "test_tool"
            assert row["pipeline_outcome"] == "allowed"
            assert row["request_id"] == "req-dict-test"
            assert row["decision_plugin"] == "dict_test_plugin"
            assert (
                row["reason"] == '[dict_test_plugin] Test with special chars: ", \n, ,'
            )
            assert row["duration_ms"] == "0"  # Zero for requests (not available)
            assert (
                row["server_name"] == "test-server"
            )  # Populated with provided server name
