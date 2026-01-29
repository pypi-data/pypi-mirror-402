"""OpenTelemetry auditing plugin for Gatekit MCP gateway.

This module provides the OtelAuditingPlugin class that logs MCP requests and responses
in OpenTelemetry format for observability correlation and cloud-native monitoring.
"""

import json
import os
import socket
import time
import uuid
import random
import hashlib
from typing import Dict, Any, Optional, List
from gatekit.plugins.auditing.base import BaseAuditingPlugin
from gatekit.utils.version import get_gatekit_version


class OtelAuditingPlugin(BaseAuditingPlugin):
    """OpenTelemetry auditing plugin for observability correlation.

    Logs MCP requests and responses in OpenTelemetry format for distributed tracing
    correlation and modern cloud-native monitoring systems.

    Features:
    - OTEL-compliant log record format
    - Trace correlation for distributed systems
    - Configurable timestamp precision
    - Resource attributes for service identification
    - Severity mapping for different event types
    - Sampling controls for performance optimization
    - Circuit breaker for resilience
    - Size metrics and health counters
    """

    # TUI Display Metadata
    DISPLAY_NAME = "OpenTelemetry"

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Return configuration schema for OpenTelemetry auditing plugin."""
        return {
            "enabled": {
                "type": "boolean",
                "label": "Enable OpenTelemetry audit logging",
                "description": "When enabled, logs all MCP requests and responses in OpenTelemetry format for distributed tracing correlation and cloud-native monitoring. When disabled, no OpenTelemetry logging occurs.",
                "default": True,
                "required": True,
            },
            "output_file": {
                "type": "string",
                "label": "Path to OpenTelemetry output file",
                "description": "File path where OpenTelemetry audit logs will be written. Supports relative paths (relative to config directory) and absolute paths. File will be created if it doesn't exist.",
                "default": "otel.jsonl",
                "required": True,
            },
            "service_name": {
                "type": "string",
                "label": "Service Name",
                "description": "OpenTelemetry service name for resource identification",
                "default": "gatekit",
                "required": False,
            },
            "service_version": {
                "type": "string",
                "label": "Service Version",
                "description": "OpenTelemetry service version (auto-detected if not specified)",
                "required": False,
            },
            "service_namespace": {
                "type": "string",
                "label": "Service Namespace",
                "description": "OpenTelemetry service namespace for logical grouping",
                "default": "gatekit",
                "required": False,
            },
            "deployment_environment": {
                "type": "string",
                "label": "Deployment Environment",
                "description": "Environment name for OpenTelemetry resource attributes",
                "default": "production",
                "required": False,
            },
            "include_trace_correlation": {
                "type": "boolean",
                "label": "Include Trace Correlation",
                "description": "Enable trace correlation for distributed tracing systems",
                "default": True,
                "required": False,
            },
            "timestamp_precision": {
                "type": "enum",
                "label": "Timestamp Precision",
                "description": "Precision level for OpenTelemetry timestamps",
                "options": ["nanoseconds", "microseconds", "milliseconds"],
                "display_labels": {
                    "nanoseconds": "Nanoseconds",
                    "microseconds": "Microseconds",
                    "milliseconds": "Milliseconds",
                },
                "default": "nanoseconds",
                "required": False,
            },
            "resource_attributes": {
                "type": "object",
                "label": "Additional Resource Attributes",
                "description": "Additional OpenTelemetry resource attributes",
                "default": {},
                "required": False,
            },
            "sampling_rate": {
                "type": "number",
                "label": "Global Sampling Rate",
                "description": "Global sampling rate for events (0.0 to 1.0)",
                "default": 1.0,
                "min": 0.0,
                "max": 1.0,
                "required": False,
            },
            "event_sampling_rates": {
                "type": "object",
                "label": "Event-Specific Sampling Rates",
                "description": "Sampling rates for specific event types",
                "default": {},
                "required": False,
            },
            "circuit_breaker_threshold": {
                "type": "number",
                "label": "Circuit Breaker Threshold",
                "description": "Number of consecutive failures before circuit breaker opens",
                "default": 10,
                "min": 1,
                "required": False,
            },
            "circuit_breaker_enabled": {
                "type": "boolean",
                "label": "Enable Circuit Breaker",
                "description": "Enable circuit breaker for resilience",
                "default": True,
                "required": False,
            },
            "metadata_allowlist": {
                "type": "list",
                "label": "Metadata Allowlist",
                "description": "List of allowed metadata keys (null allows all)",
                "items": {"type": "string"},
                "required": False,
            },
            "max_reason_length": {
                "type": "number",
                "label": "Maximum Reason Length",
                "description": "Maximum length for reason text before truncation",
                "default": 1000,
                "min": 0,
                "required": False,
            },
            "max_string_length": {
                "type": "number",
                "label": "Maximum String Length",
                "description": "Maximum length for string values before truncation",
                "default": 2000,
                "min": 0,
                "required": False,
            },
            "redact_reason": {
                "type": "boolean",
                "label": "Redact Reason Text",
                "description": "Redact reason text for security (replaces with hash)",
                "default": False,
                "required": False,
            },
            "redaction_keywords": {
                "type": "list",
                "label": "Redaction Keywords",
                "description": "Keywords that identify redaction operations",
                "items": {"type": "string"},
                "default": ["redact", "censor", "filter", "block", "remove"],
                "required": False,
            },
            "health_counter_interval": {
                "type": "number",
                "label": "Health Counter Interval",
                "description": "Interval for health counter emissions",
                "default": 100,
                "min": 1,
                "required": False,
            },
            "health_counter_time_based": {
                "type": "boolean",
                "label": "Time-Based Health Counters",
                "description": "Use time-based instead of event-based health counters",
                "default": False,
                "required": False,
            },
            "max_metadata_entries": {
                "type": "number",
                "label": "Maximum Metadata Entries",
                "description": "Maximum number of metadata entries to include",
                "default": 50,
                "min": 1,
                "required": False,
            },
        }

    @classmethod
    def describe_status(cls, config: Dict[str, Any]) -> str:
        """Generate status description from OpenTelemetry configuration."""
        if not config or not config.get("enabled", False):
            return "Export audit logs to OpenTelemetry format"

        output_file = config.get("output_file", "otel.jsonl")
        service_name = config.get("service_name", "gatekit")
        include_trace_correlation = config.get("include_trace_correlation", True)

        # Check if file exists and get size (if available)
        try:
            import os

            if os.path.exists(output_file):
                size_mb = os.path.getsize(output_file) / 1_048_576
                trace_text = "with traces" if include_trace_correlation else "no traces"
                return f"{output_file} ({size_mb:.1f}MB, {service_name}, {trace_text})"
            else:
                trace_text = "with traces" if include_trace_correlation else "no traces"
                return f"{output_file} (not created, {service_name}, {trace_text})"
        except:
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
            except:
                pass
            return ["Configure"]
        return ["Setup"]

    # Class constants for severity mapping
    SEVERITY_TEXT_MAPPING = {
        "REQUEST": "INFO",
        "RESPONSE": "INFO",
        "SECURITY_BLOCK": "WARN",
        "REDACTION": "WARN",
        "MODIFICATION": "WARN",
        "ERROR": "ERROR",
        "UPSTREAM_ERROR": "ERROR",
        "NOTIFICATION": "INFO",
        "TOOLS_FILTERED": "DEBUG",
    }

    SEVERITY_NUMBER_MAPPING = {
        "REQUEST": 9,  # INFO
        "RESPONSE": 9,  # INFO
        "SECURITY_BLOCK": 13,  # WARN
        "REDACTION": 13,  # WARN
        "MODIFICATION": 13,  # WARN
        "ERROR": 17,  # ERROR
        "UPSTREAM_ERROR": 17,  # ERROR
        "NOTIFICATION": 9,  # INFO
        "TOOLS_FILTERED": 5,  # DEBUG
    }

    # Type annotations for class attributes
    service_name: str
    service_version: str
    service_namespace: str
    deployment_environment: str
    include_trace_correlation: bool
    timestamp_precision: str
    resource_attributes: Dict[str, Any]

    # Sampling controls
    sampling_rate: float
    event_sampling_rates: Dict[str, float]

    # Circuit breaker
    circuit_breaker_threshold: int
    circuit_breaker_enabled: bool

    # Metadata security
    metadata_allowlist: Optional[list]

    # Health counters
    emission_count: int
    emit_failures: int
    health_counter_interval: int

    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenTelemetry auditing plugin with configuration.

        Args:
            config: Plugin configuration dictionary with OTEL-specific options:
                   - service_name: Service name (default: "gatekit")
                   - service_version: Service version (default: auto-detected)
                   - service_namespace: Service namespace (default: "gatekit")
                   - deployment_environment: Environment name (default: "production")
                   - include_trace_correlation: Enable trace correlation (default: True)
                   - timestamp_precision: "nanoseconds", "microseconds", "milliseconds" (default: "nanoseconds")
                   - resource_attributes: Additional resource attributes (default: {})
                   Plus all BaseAuditingPlugin options (output_file, etc.)

        Raises:
            ValueError: If configuration is invalid
            TypeError: If configuration has wrong types
        """
        # Initialize base class first
        super().__init__(config)

        # OTEL-specific configuration
        self.service_name = config.get("service_name", "gatekit")
        self.service_version = config.get("service_version") or get_gatekit_version()
        self.service_namespace = config.get("service_namespace", "gatekit")
        self.deployment_environment = config.get("deployment_environment", "production")
        self.include_trace_correlation = config.get("include_trace_correlation", True)
        self.timestamp_precision = config.get("timestamp_precision", "nanoseconds")
        self.resource_attributes = config.get("resource_attributes", {})

        # Size limits and safety options
        self.max_reason_length = config.get("max_reason_length", 1000)
        self.max_string_length = config.get("max_string_length", 2000)
        self.redact_reason = config.get("redact_reason", False)
        self.redaction_keywords = config.get(
            "redaction_keywords", ["redact", "censor", "filter", "block", "remove"]
        )

        # Testability: injectable functions
        self.clock_fn = config.get("clock_fn", time.time_ns)
        self.trace_id_fn = config.get("trace_id_fn", self._generate_trace_id)
        self.span_id_fn = config.get("span_id_fn", self._generate_span_id)
        self.random_fn = config.get(
            "random_fn", random.random
        )  # For deterministic testing

        # Extensibility: optional attribute enrichment hook
        self.attribute_enrichment_hook = config.get("attribute_enrichment_hook")

        # Sampling controls for performance optimization
        self.sampling_rate = config.get("sampling_rate", 1.0)  # Default: log all events
        self.event_sampling_rates = config.get("event_sampling_rates", {})

        # Circuit breaker for resilience
        self.circuit_breaker_threshold = config.get("circuit_breaker_threshold", 10)
        self.circuit_breaker_enabled = config.get("circuit_breaker_enabled", True)
        self._consecutive_failures = 0
        self._circuit_open = False

        # Metadata security allowlist
        self.metadata_allowlist = config.get(
            "metadata_allowlist"
        )  # None means allow all

        # Health counters for monitoring
        self.emission_count = 0
        self.emit_failures = 0
        self.health_counter_interval = config.get("health_counter_interval", 100)
        self.health_counter_time_based = config.get("health_counter_time_based", False)
        self._last_health_counter_time = time.time()

        # Metadata security controls
        self.max_metadata_entries = config.get(
            "max_metadata_entries", 50
        )  # Defense-in-depth

        # Validate configuration
        self._validate_config()

        # Cache system info to avoid repeated lookups (must be before _build_resource)
        self._hostname = socket.gethostname()
        self._pid = os.getpid()

        # Build resource dict once for performance
        self._service_instance_uid = str(uuid.uuid4())  # Unique per plugin instance
        self._resource_attrs = self._build_resource()

    def _validate_config(self):
        """Validate OTEL configuration."""
        valid_precisions = ["nanoseconds", "microseconds", "milliseconds"]
        if self.timestamp_precision not in valid_precisions:
            raise ValueError(f"timestamp_precision must be one of: {valid_precisions}")

        if not isinstance(self.service_name, str) or not self.service_name.strip():
            raise ValueError("service_name must be a non-empty string")

        if not isinstance(self.include_trace_correlation, bool):
            raise ValueError("include_trace_correlation must be a boolean")

        if not isinstance(self.resource_attributes, dict):
            raise ValueError("resource_attributes must be a dictionary")

        if not isinstance(self.max_reason_length, int) or self.max_reason_length < 0:
            raise ValueError("max_reason_length must be a non-negative integer")

        if not isinstance(self.max_string_length, int) or self.max_string_length < 0:
            raise ValueError("max_string_length must be a non-negative integer")

        if not isinstance(self.redact_reason, bool):
            raise ValueError("redact_reason must be a boolean")

        if not isinstance(self.redaction_keywords, list) or not all(
            isinstance(kw, str) for kw in self.redaction_keywords
        ):
            raise ValueError("redaction_keywords must be a list of strings")

        # Validate sampling controls
        if not isinstance(self.sampling_rate, (int, float)) or not (
            0.0 <= self.sampling_rate <= 1.0
        ):
            raise ValueError("sampling_rate must be a number between 0.0 and 1.0")

        if not isinstance(self.event_sampling_rates, dict):
            raise ValueError("event_sampling_rates must be a dictionary")

        for event_type, rate in self.event_sampling_rates.items():
            if not isinstance(rate, (int, float)) or not (0.0 <= rate <= 1.0):
                raise ValueError(
                    f"sampling rate for '{event_type}' must be between 0.0 and 1.0"
                )

        # Validate circuit breaker settings
        if (
            not isinstance(self.circuit_breaker_threshold, int)
            or self.circuit_breaker_threshold < 1
        ):
            raise ValueError("circuit_breaker_threshold must be a positive integer")

        if not isinstance(self.circuit_breaker_enabled, bool):
            raise ValueError("circuit_breaker_enabled must be a boolean")

        # Validate metadata allowlist
        if self.metadata_allowlist is not None:
            if not isinstance(self.metadata_allowlist, list) or not all(
                isinstance(key, str) for key in self.metadata_allowlist
            ):
                raise ValueError("metadata_allowlist must be a list of strings")

        # Validate health counter settings
        if (
            not isinstance(self.health_counter_interval, int)
            or self.health_counter_interval < 1
        ):
            raise ValueError("health_counter_interval must be a positive integer")

        if not isinstance(self.health_counter_time_based, bool):
            raise ValueError("health_counter_time_based must be a boolean")

        # Validate metadata controls
        if (
            not isinstance(self.max_metadata_entries, int)
            or self.max_metadata_entries < 1
        ):
            raise ValueError("max_metadata_entries must be a positive integer")

    def _format_request_entry(self, data: Dict[str, Any]) -> str:
        """Format extracted request data into OTEL log entry.

        Args:
            data: Dictionary containing extracted request data

        Returns:
            str: OTEL-formatted log message or empty string if sampled out
        """
        # Use event type from extracted data, but check for OTEL-specific modifications
        event_type = data["event_type"]

        # OTEL uses different names for some event types
        if event_type == "REQUEST_MODIFIED":
            event_type = (
                "REDACTION" if self._is_redaction(data["reason"]) else "MODIFICATION"
            )

        # Check sampling - return empty string if sampled out
        if not self._should_sample_event(event_type):
            return ""

        # Build event data
        event_data = {
            "event_type": event_type,
            "method": data.get("method", ""),
            "request_id": data.get("request_id"),
            "status": "ALLOWED" if data["is_allowed"] else "BLOCKED",
            "server_name": data["server_name"],
        }

        # Add tool name if available
        if "tool_name" in data:
            event_data["tool"] = data["tool_name"]
        elif event_type == "SECURITY_BLOCK" and data.get("method") == "tools/call":
            # For security blocks on tools/call, always include a tool name (even if unknown)
            event_data["tool"] = "unknown"

        # Add plugin information
        if data["plugin_name"] != "unknown":
            event_data["plugin"] = data["plugin_name"]

        # Add decision reason with optional redaction/truncation
        if data["reason"]:
            event_data["reason"] = self._process_reason(data["reason"])

        # Add size metrics for request payload if available
        if "params" in data:
            # Calculate size from params for consistency
            event_data["request_size_bytes"] = (
                len(json.dumps(data["params"])) if data["params"] else 0
            )

        # Extract trace context to event_data for correlation
        if data.get("metadata") and "trace_context" in data["metadata"]:
            event_data["trace_context"] = data["metadata"]["trace_context"]

        # Prepare sanitized metadata separately to avoid leakage
        sanitized_metadata = None
        if data.get("metadata"):
            core_fields = {
                "event_type",
                "method",
                "request_id",
                "status",
                "server_name",
                "tool",
                "plugin",
                "reason",
                "trace_context",
            }
            filtered_metadata = {
                k: v
                for k, v in data["metadata"].items()
                if k != "plugin" and k not in core_fields
            }
            # Apply allowlist filtering for security
            allowlist_filtered = self._filter_metadata_allowlist(filtered_metadata)
            sanitized_metadata = self._sanitize_metadata(allowlist_filtered)

        return self._format_otel_record(event_data, sanitized_metadata)

    def _format_response_entry(self, data: Dict[str, Any]) -> str:
        """Format extracted response data into OTEL log entry.

        Args:
            data: Dictionary containing extracted response data

        Returns:
            str: OTEL-formatted log message or empty string if sampled out
        """
        # Use event type from extracted data, handle OTEL-specific naming
        event_type = data["event_type"]

        # OTEL uses different names for some event types
        if event_type == "RESPONSE_MODIFIED":
            # Check for specific modification types
            if data.get("method") == "tools/list":
                event_type = "TOOLS_FILTERED"
            else:
                # Use same keyword heuristic as request path to distinguish types
                event_type = (
                    "REDACTION"
                    if self._is_redaction(data["reason"])
                    else "MODIFICATION"
                )
        elif data.get("response_status") == "error":
            # Classify error type
            error_code = data.get("error_code", 0)
            if isinstance(error_code, int) and error_code < -32000:
                event_type = "UPSTREAM_ERROR"
            else:
                event_type = "ERROR"

        # Check sampling - return empty string if sampled out
        if not self._should_sample_event(event_type):
            return ""

        # Build event data
        event_data = {
            "event_type": event_type,
            "method": data.get("method", ""),  # Include method from original request
            "request_id": data.get("request_id"),
            "server_name": data["server_name"],
        }

        # Set status based on event type
        if event_type == "RESPONSE":
            event_data["status"] = "SUCCESS"
        elif "ERROR" in event_type:
            event_data["status"] = "ERROR"
        elif event_type == "SECURITY_BLOCK":
            event_data["status"] = "BLOCKED"
        else:
            event_data["status"] = "MODIFIED"

        # Add error details if present
        if "error_code" in data:
            event_data["error_code"] = data["error_code"]
            event_data["error_message"] = data.get("error_message", "")

        # Add plugin information
        if data["plugin_name"] != "unknown":
            event_data["plugin"] = data["plugin_name"]

        # Add decision reason with optional redaction/truncation
        if data["reason"]:
            event_data["reason"] = self._process_reason(data["reason"])

        # Add duration if available
        if "duration_ms" in data:
            event_data["duration_ms"] = data["duration_ms"]

        # Add size metrics for response payload if we have result/error
        if "result" in data or "error_code" in data:
            # Calculate approximate size
            if "result" in data:
                event_data["response_size_bytes"] = (
                    len(json.dumps(data["result"])) if data["result"] else 0
                )
            else:
                event_data["response_size_bytes"] = len(
                    json.dumps(
                        {
                            "code": data["error_code"],
                            "message": data.get("error_message", ""),
                        }
                    )
                )

        # Extract trace context to event_data for correlation
        if data.get("metadata") and "trace_context" in data["metadata"]:
            event_data["trace_context"] = data["metadata"]["trace_context"]

        # Prepare sanitized metadata separately to avoid leakage
        sanitized_metadata = None
        if data.get("metadata"):
            core_fields = {
                "event_type",
                "method",
                "request_id",
                "status",
                "server_name",
                "error_code",
                "error_message",
                "plugin",
                "reason",
                "duration_ms",
                "trace_context",
            }
            filtered_metadata = {
                k: v for k, v in data["metadata"].items() if k not in core_fields
            }
            # Apply allowlist filtering for security
            allowlist_filtered = self._filter_metadata_allowlist(filtered_metadata)
            sanitized_metadata = self._sanitize_metadata(allowlist_filtered)

        return self._format_otel_record(event_data, sanitized_metadata)

    def _format_notification_entry(self, data: Dict[str, Any]) -> str:
        """Format extracted notification data into OTEL log entry.

        Args:
            data: Dictionary containing extracted notification data

        Returns:
            str: OTEL-formatted log message or empty string if sampled out
        """
        event_type = "NOTIFICATION"

        # Check sampling - return empty string if sampled out
        if not self._should_sample_event(event_type):
            return ""

        # Build event data
        event_data = {
            "event_type": event_type,
            "method": data.get("method", ""),
            "status": "NOTIFICATION",
            "server_name": data["server_name"],
        }

        # Add plugin information
        if data["plugin_name"] != "unknown":
            event_data["plugin"] = data["plugin_name"]

        # Add decision reason with optional redaction/truncation
        if data["reason"]:
            event_data["reason"] = self._process_reason(data["reason"])

        # Extract trace context to event_data for correlation
        if data.get("metadata") and "trace_context" in data["metadata"]:
            event_data["trace_context"] = data["metadata"]["trace_context"]

        # Prepare sanitized metadata separately to avoid leakage
        sanitized_metadata = None
        if data.get("metadata"):
            core_fields = {
                "event_type",
                "method",
                "status",
                "server_name",
                "plugin",
                "reason",
                "trace_context",
            }
            filtered_metadata = {
                k: v
                for k, v in data["metadata"].items()
                if k != "plugin" and k not in core_fields
            }
            # Apply allowlist filtering for security
            allowlist_filtered = self._filter_metadata_allowlist(filtered_metadata)
            sanitized_metadata = self._sanitize_metadata(allowlist_filtered)

        return self._format_otel_record(event_data, sanitized_metadata)

    def _format_otel_record(
        self,
        event_data: Dict[str, Any],
        sanitized_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Format Gatekit event as OTEL log record.

        Args:
            event_data: Event data dictionary from Gatekit
            sanitized_metadata: Optional sanitized metadata dictionary

        Returns:
            str: Formatted OTEL log record as JSON string
        """
        current_time_ns = self.clock_fn()
        event_type = event_data.get("event_type", "EVENT")

        log_record = {
            "time_unix_nano": self._format_timestamp_nano_from_ns(current_time_ns),
            "observed_time_unix_nano": self._format_timestamp_nano_from_ns(
                current_time_ns
            ),
            "severity_text": self._map_severity_text(event_type),
            "severity_number": self._map_severity_number(event_type),
            "body": self._format_body(
                event_type,
                event_data.get("method", ""),
                event_data.get("status", ""),
                event_data.get("reason"),  # Already processed by _process_reason
            ),
            "attributes": self._format_attributes(event_data, sanitized_metadata),
            "resource": self._resource_attrs,
        }

        # Add trace correlation if available and enabled
        if self.include_trace_correlation:
            trace_context = self._get_trace_context(event_data)
            if trace_context:
                log_record.update(trace_context)
            else:
                # Auto-generate trace context when enabled but not provided
                log_record.update(
                    {"trace_id": self.trace_id_fn(), "span_id": self.span_id_fn()}
                )

        try:
            result = json.dumps(log_record, ensure_ascii=False)
            # Update circuit breaker on success
            self._handle_circuit_breaker(success=True)
            return result
        except (TypeError, ValueError) as e:
            # Update circuit breaker on failure
            self._handle_circuit_breaker(success=False)

            # Fallback minimal record if serialization fails
            fallback_record = {
                "time_unix_nano": self.clock_fn(),
                "severity_text": "ERROR",
                "severity_number": 17,
                "body": f"OTEL serialization error: {str(e)}",
                "attributes": {"gatekit.error": "serialization_failed"},
                "resource": {"service.name": self.service_name},
            }
            return json.dumps(fallback_record, ensure_ascii=False)

    def _format_timestamp_nano_from_ns(self, timestamp_ns: int) -> int:
        """Format timestamp from nanoseconds with precision truncation for OTLP compliance.

        Args:
            timestamp_ns: Timestamp in nanoseconds since Unix epoch

        Returns:
            int: Nanoseconds since Unix epoch with appropriate precision
        """
        # Apply precision truncation based on config
        if self.timestamp_precision == "nanoseconds":
            return timestamp_ns
        elif self.timestamp_precision == "microseconds":
            # Truncate to microsecond precision
            return (timestamp_ns // 1_000) * 1_000
        else:  # milliseconds
            # Truncate to millisecond precision
            return (timestamp_ns // 1_000_000) * 1_000_000

    def _map_severity_text(self, event_type: str) -> str:
        """Map Gatekit event type to OTEL severity text.

        Args:
            event_type: Gatekit event type

        Returns:
            str: OTEL severity text
        """
        return self.SEVERITY_TEXT_MAPPING.get(event_type, "INFO")

    def _map_severity_number(self, event_type: str) -> int:
        """Map Gatekit event type to OTEL severity number (1-24).

        Args:
            event_type: Gatekit event type

        Returns:
            int: OTEL severity number
        """
        return self.SEVERITY_NUMBER_MAPPING.get(event_type, 9)

    def _format_body(
        self, event_type: str, method: str, status: str, reason: Optional[str]
    ) -> str:
        """Format log message body.

        Args:
            event_type: Type of event
            method: MCP method
            status: Event status
            reason: Optional reason text

        Returns:
            str: Formatted body message
        """
        if event_type == "REQUEST":
            return f"MCP {method} request - {status}"
        elif event_type == "RESPONSE":
            return f"MCP {method} response - {status}"
        elif event_type == "SECURITY_BLOCK":
            return f"Security block: {reason or 'Unknown'}"
        elif event_type in ["REDACTION", "MODIFICATION"]:
            return f"Content {event_type.lower()}: {reason or 'Unknown'}"
        else:
            return f"{event_type}: {method} - {status}"

    def _format_attributes(
        self,
        event_data: Dict[str, Any],
        sanitized_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Format event attributes with OTEL namespace.

        Args:
            event_data: Event data dictionary
            sanitized_metadata: Optional sanitized metadata dictionary

        Returns:
            Dict[str, Any]: OTEL attributes
        """
        attributes = {}

        # Map Gatekit fields to OTEL attributes with namespace
        field_mappings = {
            "event_type": "gatekit.event_type",
            "method": "gatekit.method",
            "tool": "gatekit.tool",
            "status": "gatekit.status",
            "request_id": "gatekit.request_id",
            "plugin": "gatekit.plugin",
            "reason": "gatekit.reason",
            "duration_ms": "gatekit.duration_ms",
            "server_name": "gatekit.server_name",
            "error_code": "gatekit.error_code",
            "error_message": "gatekit.error_message",
            "request_size_bytes": "gatekit.request_size_bytes",
            "response_size_bytes": "gatekit.response_size_bytes",
        }

        for event_field, otel_field in field_mappings.items():
            value = event_data.get(event_field)
            if value is not None:
                attributes[otel_field] = value

        # Add sanitized metadata with proper namespace
        if sanitized_metadata:
            for key, value in sanitized_metadata.items():
                attributes[f"gatekit.metadata.{key}"] = value

        # Apply optional attribute enrichment hook for extensibility
        if self.attribute_enrichment_hook:
            try:
                enriched_attributes = self.attribute_enrichment_hook(
                    attributes, event_data
                )
                if isinstance(enriched_attributes, dict):
                    attributes.update(enriched_attributes)
            except Exception:
                # Silently ignore enrichment hook errors to avoid breaking the audit pipeline
                pass

        # Add health counters if interval reached
        health_counters = self._update_health_counters()
        if health_counters:
            attributes.update(health_counters)

        return attributes

    def _build_resource(self) -> Dict[str, str]:
        """Format OTEL resource attributes.

        Returns:
            Dict[str, str]: OTEL resource attributes
        """
        resource = {
            "service.name": self.service_name,
            "service.version": self.service_version,
            "service.namespace": self.service_namespace,
            "service.instance.id": f"{self._hostname}-{self._pid}",
            "service.instance.uid": self._service_instance_uid,
            "deployment.environment": self.deployment_environment,
            "host.name": self._hostname,
            "process.pid": str(self._pid),
            "telemetry.sdk.name": "gatekit",
            "telemetry.sdk.version": self.service_version,
            "telemetry.sdk.language": "python",
        }

        # Add any additional resource attributes
        resource.update(self.resource_attributes)

        return resource

    def _get_trace_context(
        self, event_data: Dict[str, Any]
    ) -> Optional[Dict[str, str]]:
        """Get trace context from event data if trace correlation is enabled.

        Args:
            event_data: Event data that might contain trace context

        Returns:
            Optional[Dict[str, str]]: Trace context or None
        """
        if not self.include_trace_correlation:
            return None

        # Check for trace context in event data
        if "trace_context" in event_data:
            trace_context = event_data["trace_context"]
            return {
                "trace_id": trace_context.get("trace_id"),
                "span_id": trace_context.get("span_id"),
            }

        # Check for direct trace fields in event data
        if "trace_id" in event_data or "span_id" in event_data:
            return {
                "trace_id": event_data.get("trace_id"),
                "span_id": event_data.get("span_id"),
            }

        return None

    def _generate_trace_id(self) -> str:
        """Generate OTEL-compliant trace ID.

        Returns:
            str: 32-character hex string representing 16-byte trace ID
        """
        # 16-byte random value as 32-character hex string
        return uuid.uuid4().hex

    def _generate_span_id(self) -> str:
        """Generate OTEL-compliant span ID.

        Returns:
            str: 16-character hex string representing 8-byte span ID
        """
        # 8-byte random value as 16-character hex string
        return uuid.uuid4().hex[:16]

    def _process_reason(self, reason: str) -> str:
        """Process reason text with redaction and truncation options.

        Args:
            reason: Original reason text

        Returns:
            str: Processed reason text
        """
        if self.redact_reason:
            # Return redacted message with hash for audit reconciliation
            reason_hash = self._hash_reason(reason)
            return f"[REDACTED:hash:{reason_hash}]"

        # Truncate if too long
        if len(reason) > self.max_reason_length:
            return reason[: self.max_reason_length] + "..."

        return reason

    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize metadata to ensure JSON serialization safety.

        Args:
            metadata: Raw metadata dictionary

        Returns:
            Dict[str, Any]: Sanitized metadata safe for JSON serialization,
                          limited to max_metadata_entries for defense-in-depth
        """
        sanitized = {}
        entries_processed = 0

        for key, value in metadata.items():
            # Defense-in-depth: limit number of metadata entries
            if entries_processed >= self.max_metadata_entries:
                # Add indicator that entries were truncated
                sanitized["_gatekit_metadata_truncated"] = (
                    f"Limited to {self.max_metadata_entries} entries"
                )
                break

            # Truncate key if too long
            safe_key = key[:100] if len(str(key)) > 100 else key

            try:
                # Test JSON serialization
                json.dumps(value)
                # Truncate strings if too long
                if isinstance(value, str) and len(value) > self.max_string_length:
                    sanitized[safe_key] = value[: self.max_string_length] + "..."
                else:
                    sanitized[safe_key] = value
            except (TypeError, ValueError):
                # Convert non-serializable values to safe string representation
                str_value = str(value)
                if len(str_value) > self.max_string_length:
                    str_value = str_value[: self.max_string_length] + "..."
                sanitized[safe_key] = f"[CONVERTED]{str_value}"

            entries_processed += 1

        return sanitized

    def _is_redaction(self, reason: Optional[str]) -> bool:
        """Check if a reason string indicates redaction based on configured keywords.

        Args:
            reason: Reason text to check

        Returns:
            bool: True if reason indicates redaction, False otherwise
        """
        if not reason or not self.redaction_keywords:
            return False

        reason_lower = reason.lower()
        return any(
            keyword.lower() in reason_lower for keyword in self.redaction_keywords
        )

    def _should_sample_event(self, event_type: str) -> bool:
        """Determine if an event should be sampled based on configured rates.

        Args:
            event_type: The type of event being logged

        Returns:
            bool: True if event should be logged, False if it should be sampled out
        """
        # Check circuit breaker first
        if self.circuit_breaker_enabled and self._circuit_open:
            return False

        # Early exit optimization: if global sampling is 0 and no event-specific rates, skip all
        if self.sampling_rate == 0.0 and not self.event_sampling_rates:
            return False

        # Use event-specific sampling rate if configured, otherwise use global rate
        sampling_rate = self.event_sampling_rates.get(event_type, self.sampling_rate)

        # Always sample if rate is 1.0 or higher
        if sampling_rate >= 1.0:
            return True

        # Never sample if rate is 0.0 or lower
        if sampling_rate <= 0.0:
            return False

        # Probabilistic sampling
        return self.random_fn() < sampling_rate

    def _calculate_payload_size(self, obj: Any) -> int:
        """Calculate approximate byte size of a payload for size metrics.

        Note: This is an approximate size based on JSON encoding and may differ
        from actual wire protocol size due to compression, binary encoding, or
        other transport-specific optimizations.

        Args:
            obj: Object to measure (request/response)

        Returns:
            int: Approximate byte size of the object when serialized
        """
        try:
            if hasattr(obj, "params") and obj.params:
                return len(json.dumps(obj.params, ensure_ascii=False).encode("utf-8"))
            elif hasattr(obj, "result") and obj.result:
                return len(json.dumps(obj.result, ensure_ascii=False).encode("utf-8"))
            else:
                return len(
                    json.dumps(
                        obj.__dict__ if hasattr(obj, "__dict__") else str(obj),
                        ensure_ascii=False,
                    ).encode("utf-8")
                )
        except (TypeError, AttributeError):
            # Fallback to string length if JSON serialization fails
            return len(str(obj).encode("utf-8"))

    def _handle_circuit_breaker(self, success: bool) -> None:
        """Handle circuit breaker state based on success/failure.

        Args:
            success: Whether the operation was successful
        """
        if not self.circuit_breaker_enabled:
            return

        if success:
            # Reset failure count on success
            self._consecutive_failures = 0
            self._circuit_open = False
        else:
            # Increment failure count on failure
            self._consecutive_failures += 1
            self.emit_failures += 1

            # Open circuit if threshold exceeded
            if self._consecutive_failures >= self.circuit_breaker_threshold:
                self._circuit_open = True

    def _filter_metadata_allowlist(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Filter metadata based on configured allowlist for security.

        Args:
            metadata: Original metadata dictionary

        Returns:
            Dict[str, Any]: Filtered metadata containing only allowed keys
        """
        if self.metadata_allowlist is None:
            # No allowlist configured, return all metadata
            return metadata

        # Filter to only include allowed keys
        return {
            key: value
            for key, value in metadata.items()
            if key in self.metadata_allowlist
        }

    def _hash_reason(self, reason: str) -> str:
        """Create hash of reason for audit reconciliation when redacted.

        Args:
            reason: Original reason text

        Returns:
            str: SHA-256 hash of the reason for audit reconciliation
        """
        return hashlib.sha256(reason.encode("utf-8")).hexdigest()[
            :16
        ]  # First 16 chars for brevity

    def _update_health_counters(self) -> Dict[str, int]:
        """Update and return health counter attributes if interval reached.

        Returns:
            Dict[str, int]: Health counter attributes or empty dict
        """
        self.emission_count += 1

        # Check if we should emit health counters
        should_emit = False

        if self.health_counter_time_based:
            # Time-based health counters (every N seconds)
            current_time = time.time()
            if (
                current_time - self._last_health_counter_time
                >= self.health_counter_interval
            ):
                should_emit = True
                self._last_health_counter_time = current_time
        else:
            # Event-based health counters (every N events)
            should_emit = self.emission_count % self.health_counter_interval == 0

        if should_emit:
            return {
                "gatekit.emission_count": self.emission_count,
                "gatekit.emit_failures": self.emit_failures,
                "gatekit.circuit_open": self._circuit_open,
                "gatekit.consecutive_failures": self._consecutive_failures,
            }

        return {}

    def get_circuit_breaker_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state for external monitoring.

        Returns:
            Dict[str, Any]: Circuit breaker state including enabled status,
                          open status, consecutive failures, and threshold
        """
        return {
            "enabled": self.circuit_breaker_enabled,
            "open": self._circuit_open,
            "consecutive_failures": self._consecutive_failures,
            "threshold": self.circuit_breaker_threshold,
            "total_failures": self.emit_failures,
        }


# Policy manifest for policy-based plugin discovery
POLICIES = {"otel_auditing": OtelAuditingPlugin}
