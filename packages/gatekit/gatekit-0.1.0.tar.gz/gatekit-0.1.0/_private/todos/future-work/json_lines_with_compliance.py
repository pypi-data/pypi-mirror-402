"""JSON auditing plugin for Gatekit MCP gateway.

This module provides the JsonAuditingPlugin class that logs MCP requests and responses
in JSON format for GRC platform integration and compliance automation,
supporting modern API integration and automated compliance analysis.

For JSON Lines (JSONL) format, set pretty_print=False in configuration.
"""

import json
from typing import Dict, Any, List
from datetime import datetime, timezone
from gatekit.plugins.auditing.base import BaseAuditingPlugin
from gatekit.protocol.messages import MCPRequest, MCPResponse, MCPNotification
from gatekit.plugins.interfaces import PluginResult, PipelineOutcome


# Constants for compliance metadata
API_VERSION = "1.0"
SCHEMA_VERSION = "2024.1"
REGULATORY_FRAMEWORKS = {
    "financial_services": ["SOX", "GDPR"],
    "standard": [],
    "grc_standard": ["INTERNAL_GRC"],
}


class JsonAuditingPlugin(BaseAuditingPlugin):
    """JSON auditing plugin for GRC platform integration.

    Logs MCP requests and responses in JSON format for modern GRC
    (Governance, Risk, Compliance) platform integration and compliance automation.
    Provides machine-readable format for automated compliance analysis.

    Features:
    - JSON format (use pretty_print=False for JSON Lines compatibility)
    - GRC platform integration ready
    - Compliance schema support
    - Risk metadata inclusion
    - API-compatible structured format
    - Cloud-native compliance tool integration
    """

    # TUI Display Metadata
    DISPLAY_NAME = "JSON Lines"

    @classmethod
    def describe_status(cls, config: Dict[str, Any]) -> str:
        """Generate status description from JSON logger configuration."""
        if not config or not config.get("enabled", False):
            return "Export audit logs to JSON format"

        output_file = config.get("output_file", "audit.json")
        pretty_print = config.get("pretty_print", False)

        # Check if file exists and get size (if available)
        try:
            import os

            if os.path.exists(output_file):
                size_mb = os.path.getsize(output_file) / 1_048_576
                format_str = "Pretty JSON" if pretty_print else "JSON Lines"
                return f"{output_file} ({size_mb:.1f}MB, {format_str})"
            else:
                format_str = "Pretty JSON" if pretty_print else "JSON Lines"
                return f"{output_file} (not created, {format_str})"
        except (OSError, IOError):
            return f"Logging to {output_file}"

    @classmethod
    def get_display_actions(cls, config: Dict[str, Any]) -> List[str]:
        """Return actions with log viewing capability."""
        if config and config.get("enabled", False):
            output_file = config.get("output_file", "")
            try:
                import os

                if output_file and os.path.exists(output_file):
                    return ["View Logs", "Configure"]
            except (OSError, IOError):
                pass
            return ["Configure"]
        return ["Setup"]

    # Type annotations for class attributes
    include_request_body: bool
    pretty_print: bool
    compliance_schema: str
    include_risk_metadata: bool
    api_compatible: bool
    redact_request_fields: list

    def __init__(self, config: Dict[str, Any]):
        """Initialize JSON auditing plugin with configuration.

        Args:
            config: Plugin configuration dictionary with JSON-specific options:
                   - include_request_body: Include full request parameters (default: False)
                   - pretty_print: Format JSON with indentation (default: False)
                   - compliance_schema: "standard", "grc_standard", "financial_services" (default: "standard")
                   - include_risk_metadata: Include risk assessment metadata (default: True)
                   - api_compatible: Enable API-compatible metadata fields (default: True)
                   - redact_request_fields: List of field names to redact from request_body (default: ["password", "token", "secret", "key", "auth"])
                   Plus all BaseAuditingPlugin options (output_file, etc.)

        Raises:
            ValueError: If configuration is invalid
            TypeError: If configuration has wrong types
        """
        # Initialize base class first
        super().__init__(config)

        # Track configuration overrides for traceability
        self._config_overrides = {}

        # JSON-specific configuration
        self.include_request_body = config.get("include_request_body", False)
        self.pretty_print = config.get("pretty_print", False)

        # JSON Lines format requires single-line output
        # If output_format is explicitly set to 'jsonl', enforce single-line output
        if config.get("output_format") == "jsonl":
            if self.pretty_print:
                # Track that we're overriding user configuration for traceability
                self._config_overrides["pretty_print_forced"] = True
            # Automatically disable pretty_print for JSON Lines format
            self.pretty_print = False

        # GRC Platform Integration
        self.compliance_schema = config.get("compliance_schema", "standard")
        self.include_risk_metadata = config.get("include_risk_metadata", True)
        self.api_compatible = config.get("api_compatible", True)

        # Security configuration for request body logging
        self.redact_request_fields = config.get(
            "redact_request_fields",
            ["password", "token", "secret", "key", "auth", "authorization"],
        )

        # Precompute lowercase set for efficient case-insensitive lookup
        self._redact_field_set = {field.lower() for field in self.redact_request_fields}

        # Validate configuration
        self._validate_config()

    @classmethod
    def get_json_schema(cls) -> Dict[str, Any]:
        """Return JSON Schema for JSON Lines Auditing configuration."""
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://gatekit.ai/schemas/json-lines-auditing.json",
            "type": "object",
            "description": "JSON Lines audit logging plugin configuration",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Enable JSON Lines audit logging",
                    "default": True,
                },
                "output_file": {
                    "type": "string",
                    "description": "Path to JSONL log file (supports date formatting)",
                    "default": "gatekit_audit_{date}.jsonl",
                },
                "compliance_schema": {
                    "type": "string",
                    "title": "Compliance Schema Format",
                    "enum": ["standard", "grc_standard", "financial_services"],
                    "x-enum-labels": {
                        "standard": "Standard",
                        "grc_standard": "GRC Standard",
                        "financial_services": "Financial Services",
                    },
                    "description": "Compliance schema format for audit logs",
                    "default": "standard",
                },
                "include_request_body": {
                    "type": "boolean",
                    "description": "Include request body in logs",
                    "default": False,
                },
                "include_response_body": {
                    "type": "boolean",
                    "description": "Include response body in logs",
                    "default": False,
                },
                "include_risk_metadata": {
                    "type": "boolean",
                    "description": "Include risk scoring metadata",
                    "default": True,
                },
                "api_compatible": {
                    "type": "boolean",
                    "description": "Use API-compatible field names",
                    "default": True,
                },
                "redact_request_fields": {
                    "type": "array",
                    "description": "Fields to redact from request body",
                    "items": {"type": "string"},
                    "default": [
                        "password",
                        "token",
                        "secret",
                        "key",
                        "auth",
                        "authorization",
                    ],
                },
                "buffer_size": {
                    "type": "integer",
                    "description": "Number of records to buffer before flushing",
                    "default": 100,
                    "minimum": 1,
                    "maximum": 10000,
                },
                "flush_interval": {
                    "type": "number",
                    "description": "Seconds between automatic buffer flushes",
                    "default": 5.0,
                    "minimum": 0.1,
                    "maximum": 60.0,
                },
            },
            "required": ["enabled", "output_file"],
            "additionalProperties": False,
        }

    def _validate_config(self):
        """Validate JSON configuration."""
        if self.compliance_schema not in [
            "standard",
            "grc_standard",
            "financial_services",
        ]:
            raise ValueError(
                f"Invalid compliance_schema '{self.compliance_schema}'. Must be one of: standard, grc_standard, financial_services"
            )

        if not isinstance(self.include_request_body, bool):
            raise ValueError("include_request_body must be a boolean")

        if not isinstance(self.pretty_print, bool):
            raise ValueError("pretty_print must be a boolean")

        if not isinstance(self.include_risk_metadata, bool):
            raise ValueError("include_risk_metadata must be a boolean")

        if not isinstance(self.api_compatible, bool):
            raise ValueError("api_compatible must be a boolean")

        if not isinstance(self.redact_request_fields, list):
            raise ValueError("redact_request_fields must be a list")

    def _redact_sensitive_fields(self, data: Any) -> Any:
        """Recursively redact sensitive fields from data structures.

        Args:
            data: Data structure to redact (dict, list, or primitive)

        Returns:
            Redacted copy of the data structure
        """
        if isinstance(data, dict):
            redacted = {}
            for key, value in data.items():
                if key.lower() in self._redact_field_set:
                    redacted[key] = "[REDACTED]"
                else:
                    redacted[key] = self._redact_sensitive_fields(value)
            return redacted
        elif isinstance(data, list):
            return [self._redact_sensitive_fields(item) for item in data]
        else:
            return data

    def _get_error_details(self, response: MCPResponse) -> tuple[str, int, str]:
        """Extract and normalize error details from response.

        Args:
            response: MCP response that may contain error

        Returns:
            Tuple of (event_type, error_code, error_message)
        """
        if not (hasattr(response, "error") and response.error):
            return "RESPONSE", 0, ""

        # Extract error details from dict
        error_code = response.error.get("code", 0)
        error_message = response.error.get("message", "")

        # Ensure error_code is an integer, default to 0 if None or invalid type
        if not isinstance(error_code, int):
            error_code = 0

        # Classify error type based on JSON-RPC spec
        # Server errors: -32000 to -32099
        # Protocol/client errors: other negative codes
        if -32099 <= error_code <= -32000:
            event_type = "UPSTREAM_ERROR"
        else:
            event_type = "ERROR"

        return event_type, error_code, error_message

    def _is_blocked_outcome(self, pipeline_outcome) -> bool:
        """Check if outcome represents a blocked state."""
        return pipeline_outcome in (PipelineOutcome.BLOCKED, PipelineOutcome.ERROR)

    def _get_legacy_status(self, data: Dict[str, Any]) -> str:
        """Get legacy status field for backward compatibility."""
        pipeline_outcome = data.get("pipeline_outcome")
        return "BLOCKED" if self._is_blocked_outcome(pipeline_outcome) else "ALLOWED"

    def _get_normalized_status(self, data: Dict[str, Any]) -> str:
        """Get normalized status field for backward compatibility."""
        pipeline_outcome = data.get("pipeline_outcome")
        return "blocked" if self._is_blocked_outcome(pipeline_outcome) else "allowed"

    def _build_pipeline_object(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build nested pipeline object with stage details.

        Args:
            data: Extracted common data dictionary

        Returns:
            Dict[str, Any]: Pipeline object with stages array and metadata
        """
        # Build stages array from pipeline data
        stages = []
        plugins_run = data.get("plugins_run", [])

        # Create stages based on available plugin data
        # For now, create a simplified structure since we don't have full stage details
        if plugins_run:
            decision_plugin = data.get("decision_plugin", "")
            decision_type = data.get("decision_type", "passed")

            for _i, plugin_name in enumerate(plugins_run):
                stage = {
                    "plugin": plugin_name,
                    "outcome": (
                        decision_type if plugin_name == decision_plugin else "passed"
                    ),
                    "reason": (
                        data.get("reason", "") if plugin_name == decision_plugin else ""
                    ),
                    "time_ms": 0,  # Timing data not available in current implementation
                }

                # Mark the decision-making stage
                if plugin_name == decision_plugin:
                    stage["decision"] = True

                # Mark if this stage modified content (simplified check)
                if (
                    data.get("event_type") == "REQUEST_MODIFIED"
                    and plugin_name == decision_plugin
                ):
                    stage["modified"] = True

                stages.append(stage)

        # Build pipeline object
        pipeline_obj = {
            "stages": stages,
            "total_time_ms": data.get("duration_ms", 0),
            "decision_plugin": data.get("decision_plugin", ""),
            "decision_type": data.get("decision_type", "passed"),
        }

        return pipeline_obj

    def _format_request_entry(self, data: Dict[str, Any]) -> str:
        """Format extracted request data into JSON log entry.

        Args:
            data: Dictionary containing extracted request data

        Returns:
            str: JSON-formatted log message
        """
        # Translate REQUEST_MODIFIED to MODIFICATION/REDACTION for backward compatibility
        event_type = data["event_type"]
        if event_type == "REQUEST_MODIFIED":
            # Use reason-based heuristic to distinguish between redaction and modification
            if data.get("reason") and "redact" in data["reason"].lower():
                event_type = "REDACTION"
            else:
                event_type = "MODIFICATION"

        # Build base log data from extracted common data - use extracted timestamp directly
        log_data = {
            "timestamp": data["timestamp"],  # Use the already-extracted ISO timestamp
            "event_type": event_type,
            "request_id": data.get("request_id"),
            "server_name": data["server_name"],
            "method": data.get("method"),
            "pipeline_outcome": (
                data.get("pipeline_outcome").value
                if data.get("pipeline_outcome")
                else "ALLOWED"
            ),
            "security_evaluated": data.get("security_evaluated", False),
            "pipeline": self._build_pipeline_object(data),
            "reason": data["reason"] if data["reason"] else "",
            # Legacy fields for backward compatibility
            "status": self._get_legacy_status(data),
            "decision_status": self._get_normalized_status(data),
        }

        # Add tool name if present
        if "tool_name" in data:
            log_data["tool"] = data["tool_name"]

        # Add request body if configured (with sensitive field redaction)
        if self.include_request_body and "params" in data and data["params"]:
            log_data["request_body"] = self._redact_sensitive_fields(data["params"])

        # Add compliance metadata if enabled
        if self.include_risk_metadata:
            # Create a mock request object for compliance metadata generation
            mock_request = type(
                "obj",
                (object,),
                {"method": data.get("method"), "params": data.get("params")},
            )
            mock_decision = type(
                "obj",
                (object,),
                {
                    "metadata": data.get("metadata"),
                    "reason": data.get("reason"),
                    "allowed": data.get("is_allowed", True),
                    "modified_content": (
                        data.get("params") if data.get("modified") else None
                    ),
                },
            )
            log_data["compliance_metadata"] = self._generate_compliance_metadata(
                mock_request, mock_decision, event_type, data["timestamp"]
            )

        # Add metadata from decision (excluding plugin to avoid duplication)
        if data.get("metadata"):
            filtered_metadata = {
                k: v for k, v in data["metadata"].items() if k != "plugin"
            }
            if filtered_metadata:
                log_data["plugin_metadata"] = filtered_metadata

        # Add configuration override information for traceability
        if hasattr(self, "_config_overrides") and self._config_overrides:
            log_data["config_overrides"] = self._config_overrides

        return self._format_json_output(log_data)

    def _format_response_entry(self, data: Dict[str, Any]) -> str:
        """Format extracted response data into JSON log entry.

        Args:
            data: Dictionary containing extracted response data

        Returns:
            str: JSON-formatted log message
        """
        # Determine detailed event type based on response_status and error info
        event_type = data["event_type"]
        if event_type == "RESPONSE" and data.get("response_status") == "error":
            # Need to classify error type for JSON format
            error_code = data.get("error_code", 0)
            if isinstance(error_code, int):
                if error_code == -32700:
                    event_type = "PARSE_ERROR"
                elif error_code == -32600:
                    event_type = "INVALID_REQUEST_ERROR"
                elif error_code == -32601:
                    event_type = "METHOD_NOT_FOUND_ERROR"
                elif error_code == -32602:
                    event_type = "INVALID_PARAMS_ERROR"
                elif error_code == -32603:
                    event_type = "INTERNAL_ERROR"
                elif -32099 <= error_code <= -32000:
                    event_type = "UPSTREAM_ERROR"
                else:
                    event_type = "APPLICATION_ERROR"
            else:
                event_type = "APPLICATION_ERROR"
        elif event_type == "RESPONSE_MODIFIED":
            event_type = "REDACTION"  # Keep legacy name for JSON format

        # Build base log data - use extracted timestamp directly
        log_data = {
            "timestamp": data["timestamp"],  # Use the already-extracted ISO timestamp
            "event_type": event_type,
            "request_id": data.get("request_id"),
            "server_name": data["server_name"],
            "method": data.get(
                "method", ""
            ),  # Add method from original request for correlation
            "pipeline_outcome": (
                data.get("pipeline_outcome").value
                if data.get("pipeline_outcome")
                else "ALLOWED"
            ),
            "security_evaluated": data.get("security_evaluated", False),
            "pipeline": self._build_pipeline_object(data),
            "reason": data["reason"] if data["reason"] else "",
        }

        # Add legacy status fields based on event type
        if event_type == "RESPONSE":
            log_data["status"] = "success"
            log_data["decision_status"] = "success"
        elif "ERROR" in event_type:
            log_data["status"] = "error"
            log_data["decision_status"] = "error"
        elif event_type == "SECURITY_BLOCK":
            log_data["status"] = "blocked"
            log_data["decision_status"] = "blocked"
        else:
            log_data["status"] = "modified"
            log_data["decision_status"] = "modified"

        # Add tool name if present
        if "tool_name" in data:
            log_data["tool"] = data["tool_name"]

        # Add error details if present
        if "error_code" in data:
            log_data["error_code"] = data["error_code"]
            log_data["error_message"] = data.get("error_message", "")

        # Add duration if available
        if "duration_ms" in data:
            log_data["duration_ms"] = data["duration_ms"]

        # Add compliance metadata if enabled
        if self.include_risk_metadata:
            # Create a mock response object for compliance metadata generation
            mock_response = type(
                "obj",
                (object,),
                {
                    "id": data.get("request_id"),
                    "error": (
                        {
                            "code": data.get("error_code"),
                            "message": data.get("error_message"),
                        }
                        if "error_code" in data
                        else None
                    ),
                },
            )
            mock_decision = type(
                "obj",
                (object,),
                {
                    "metadata": data.get("metadata"),
                    "reason": data.get("reason"),
                    "allowed": data.get("is_allowed", True),
                    "modified_content": (
                        data.get("result") if data.get("modified") else None
                    ),
                },
            )
            log_data["compliance_metadata"] = self._generate_compliance_metadata(
                mock_response, mock_decision, event_type, data["timestamp"]
            )

        # Add metadata from decision (excluding plugin and duration to avoid duplication)
        if data.get("metadata"):
            filtered_metadata = {
                k: v
                for k, v in data["metadata"].items()
                if k not in ["plugin", "duration_ms"]
            }
            if filtered_metadata:
                log_data["plugin_metadata"] = filtered_metadata

        return self._format_json_output(log_data)

    def _format_notification_entry(self, data: Dict[str, Any]) -> str:
        """Format extracted notification data into JSON log entry.

        Args:
            data: Dictionary containing extracted notification data

        Returns:
            str: JSON-formatted log message
        """
        # Build base log data - use extracted timestamp directly
        log_data = {
            "timestamp": data["timestamp"],  # Use the already-extracted ISO timestamp
            "event_type": data["event_type"],
            "request_id": data.get("request_id"),
            "server_name": data["server_name"],
            "method": data.get("method"),
            "pipeline_outcome": (
                data.get("pipeline_outcome").value
                if data.get("pipeline_outcome")
                else "ALLOWED"
            ),
            "security_evaluated": data.get("security_evaluated", False),
            "pipeline": self._build_pipeline_object(data),
            "reason": data["reason"] if data["reason"] else "",
        }

        # Add compliance metadata if enabled
        if self.include_risk_metadata:
            # Create a mock notification object for compliance metadata generation
            mock_notification = type(
                "obj",
                (object,),
                {"method": data.get("method"), "params": data.get("params")},
            )
            mock_decision = type(
                "obj",
                (object,),
                {
                    "metadata": data.get("metadata"),
                    "reason": data.get("reason"),
                    "allowed": data.get("is_allowed", True),
                    "modified_content": (
                        data.get("params") if data.get("modified") else None
                    ),
                },
            )
            log_data["compliance_metadata"] = self._generate_compliance_metadata(
                mock_notification, mock_decision, data["event_type"], data["timestamp"]
            )

        # Add metadata from decision (excluding plugin to avoid duplication)
        if data.get("metadata"):
            filtered_metadata = {
                k: v for k, v in data["metadata"].items() if k != "plugin"
            }
            if filtered_metadata:
                log_data["plugin_metadata"] = filtered_metadata

        # Add configuration override information for traceability
        if hasattr(self, "_config_overrides") and self._config_overrides:
            log_data["config_overrides"] = self._config_overrides

        return self._format_json_output(log_data)

    def _generate_compliance_metadata(
        self,
        message: Any,
        decision: PluginResult,
        event_type: str,
        timestamp: str = None,
    ) -> Dict[str, Any]:
        """Generate compliance metadata for the event.

        Args:
            message: MCP message
            decision: Policy decision
            event_type: Type of event
            timestamp: Optional timestamp to use (ISO format)

        Returns:
            Dict[str, Any]: Compliance metadata
        """
        # Use provided timestamp or generate new one
        if timestamp:
            audit_timestamp = timestamp
        else:
            # Fallback for cases where this is called outside log formatting
            audit_timestamp = datetime.now(timezone.utc).isoformat()

        metadata = {
            "compliance_schema": self.compliance_schema,
            "audit_timestamp": audit_timestamp,
            "event_classification": self._classify_event(event_type),
            "risk_level": self._assess_risk_level(event_type),
        }

        if self.compliance_schema == "grc_standard":
            metadata.update(
                {
                    "governance_category": self._get_governance_category(
                        message, event_type
                    ),
                    "risk_category": self._get_risk_category(event_type),
                    "compliance_framework": "INTERNAL_GRC",
                }
            )

        elif self.compliance_schema == "financial_services":
            metadata.update(
                {
                    "sox_control_objective": self._get_sox_control_objective(
                        event_type
                    ),
                    "regulatory_framework": REGULATORY_FRAMEWORKS["financial_services"],
                    "control_effectiveness": self._assess_control_effectiveness(
                        decision
                    ),
                    "audit_trail_id": self._generate_audit_trail_id(),
                    "evidence_type": self._get_evidence_type(message, event_type),
                }
            )

        # Add API-compatible fields if enabled
        if self.api_compatible:
            metadata["api_version"] = API_VERSION
            metadata["schema_version"] = SCHEMA_VERSION
            metadata["data_format"] = (
                "json_lines" if not self.pretty_print else "json_pretty"
            )

        return metadata

    def _classify_event(self, event_type: str) -> str:
        """Classify event for compliance purposes."""
        security_events = ["SECURITY_BLOCK", "REDACTION", "TOOLS_FILTERED"]
        error_events = ["ERROR", "UPSTREAM_ERROR"]

        if event_type in security_events:
            return "SECURITY_EVENT"
        elif event_type in error_events:
            return "ERROR_EVENT"
        else:
            return "OPERATIONAL_EVENT"

    def _assess_risk_level(self, event_type: str) -> str:
        """Assess risk level based on event type."""
        risk_levels = {
            "SECURITY_BLOCK": "HIGH",
            "REDACTION": "MEDIUM",
            "TOOLS_FILTERED": "LOW",
            "ERROR": "MEDIUM",
            "UPSTREAM_ERROR": "LOW",
            "REQUEST": "LOW",
            "RESPONSE": "LOW",
            "NOTIFICATION": "LOW",
        }
        return risk_levels.get(event_type, "LOW")

    def _get_governance_category(self, message: Any, event_type: str) -> str:
        """Get governance category for GRC systems."""
        if isinstance(message, MCPRequest) and message.method == "tools/call":
            return "TOOL_GOVERNANCE"
        elif event_type in ["SECURITY_BLOCK", "REDACTION"]:
            return "SECURITY_GOVERNANCE"
        else:
            return "OPERATIONAL_GOVERNANCE"

    def _get_risk_category(self, event_type: str) -> str:
        """Get risk category for GRC systems."""
        if event_type in ["SECURITY_BLOCK", "REDACTION"]:
            return "SECURITY_RISK"
        elif event_type in ["ERROR", "UPSTREAM_ERROR"]:
            return "OPERATIONAL_RISK"
        else:
            return "MINIMAL_RISK"

    def _get_sox_control_objective(self, event_type: str) -> str:
        """Get SOX control objective for financial services."""
        control_objectives = {
            "SECURITY_BLOCK": "AC-3.1 Access Enforcement",
            "REDACTION": "SC-4.1 Information in Shared Resources",
            "TOOLS_FILTERED": "AC-3.4 Discretionary Access Control",
            "ERROR": "SI-11.1 Error Handling",
            "REQUEST": "AU-12.1 Audit Generation",
            "RESPONSE": "AU-12.1 Audit Generation",
            "NOTIFICATION": "AU-12.1 Audit Generation",
        }
        return control_objectives.get(event_type, "AU-12.1 Audit Generation")

    def _assess_control_effectiveness(self, decision: PluginResult) -> str:
        """Assess control effectiveness based on decision."""
        is_allowed = getattr(decision, "allowed", True)
        if not is_allowed:
            return "EFFECTIVE"  # Control blocked unwanted action
        elif getattr(decision, "modified_content", None) is not None:
            return "PARTIALLY_EFFECTIVE"  # Control modified content
        else:
            return "NOT_APPLICABLE"  # No control action needed

    def _generate_audit_trail_id(self) -> str:
        """Generate unique audit trail ID."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")[:-3]
        return f"AG-JSON-{timestamp}"

    def _get_evidence_type(self, message: Any, event_type: str) -> str:
        """Get evidence type for audit purposes."""
        if isinstance(message, MCPRequest):
            if message.method == "tools/call":
                return "TOOL_EXECUTION_EVIDENCE"
            else:
                return "API_REQUEST_EVIDENCE"
        elif isinstance(message, MCPResponse):
            return "API_RESPONSE_EVIDENCE"
        elif isinstance(message, MCPNotification):
            return "SYSTEM_NOTIFICATION_EVIDENCE"
        else:
            return "UNKNOWN_EVIDENCE"

    def _format_json_output(self, log_data: Dict[str, Any]) -> str:
        """Format log data as JSON output.

        Args:
            log_data: Log data dictionary

        Returns:
            str: JSON-formatted string

        Raises:
            TypeError: If the data cannot be serialized to JSON
        """
        try:
            result = json.dumps(
                log_data,
                ensure_ascii=False,
                indent=2 if self.pretty_print else None,
                separators=(",", ": ") if self.pretty_print else (",", ":"),
            )
            # Always add newline for proper log framing (both compact and pretty modes)
            result += "\n"
            return result
        except (TypeError, ValueError) as e:
            # If serialization fails, try to create a safe version
            safe_log_data = {
                "error": "JSON serialization failed",
                "error_details": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": log_data.get("event_type", "UNKNOWN"),
            }
            # Add safe fields that we know can be serialized
            for key in [
                "request_id",
                "method",
                "status",
                "decision_status",
                "server_name",
            ]:
                if key in log_data and isinstance(
                    log_data[key], (str, int, float, bool, type(None))
                ):
                    safe_log_data[key] = log_data[key]

            result = json.dumps(
                safe_log_data,
                ensure_ascii=False,
                indent=2 if self.pretty_print else None,
                separators=(",", ": ") if self.pretty_print else (",", ":"),
            )
            # Always add newline for proper log framing (both compact and pretty modes)
            result += "\n"
            return result


# Handler manifest for handler-based plugin discovery
HANDLERS = {"json_auditing": JsonAuditingPlugin}
