"""CEF (Common Event Format) auditing plugin for Gatekit MCP gateway.

This module provides the CefAuditingPlugin class that logs MCP requests and responses
in CEF format for SIEM integration and compliance monitoring.
"""

from typing import Dict, Any, Optional, List
from gatekit.plugins.auditing.base import BaseAuditingPlugin
from gatekit.utils.version import get_gatekit_version


# CEF Event Type Mappings
CEF_EVENT_MAPPINGS = {
    "REQUEST": {"event_id": "100", "severity": 6, "name": "MCP Request"},
    "RESPONSE": {"event_id": "101", "severity": 6, "name": "MCP Response"},
    "SECURITY_BLOCK": {"event_id": "200", "severity": 8, "name": "Security Block"},
    "REDACTION": {"event_id": "201", "severity": 7, "name": "Content Redaction"},
    "MODIFICATION": {"event_id": "203", "severity": 7, "name": "Content Modification"},
    "ERROR": {"event_id": "400", "severity": 9, "name": "System Error"},
    "UPSTREAM_ERROR": {"event_id": "401", "severity": 8, "name": "Upstream Error"},
    "TOOLS_FILTERED": {"event_id": "202", "severity": 7, "name": "Tools Filtered"},
    "NOTIFICATION": {"event_id": "102", "severity": 4, "name": "MCP Notification"},
}

# Default mapping for unknown event types
DEFAULT_CEF_EVENT_MAPPING = {"event_id": "999", "severity": 5, "name": "Unknown Event"}


class CefAuditingPlugin(BaseAuditingPlugin):
    """CEF (Common Event Format) auditing plugin.

    Logs MCP requests and responses in CEF format for SIEM integration.
    CEF is an industry-standard format widely accepted by security information
    and event management systems.

    Features:
    - Industry-standard CEF format for universal SIEM acceptance
    - Compliance-ready event structure
    - Security event classification and severity scoring
    - Configurable compliance tags and extensions
    - Risk scoring and regulatory field support
    """

    # TUI Display Metadata
    DISPLAY_NAME = "CEF"

    @classmethod
    def describe_status(cls, config: Dict[str, Any]) -> str:
        """Generate status description from CEF configuration."""
        if not config or not config.get("enabled", False):
            return "Export audit logs to CEF format"

        output_file = config.get("output_file", "audit.cef")
        cef_config = config.get("cef_config", {})
        device_vendor = cef_config.get("device_vendor", "Gatekit")

        # Check if file exists and get size (if available)
        try:
            import os

            if os.path.exists(output_file):
                size_mb = os.path.getsize(output_file) / 1_048_576
                return f"{output_file} ({size_mb:.1f}MB, {device_vendor} CEF)"
            else:
                return f"{output_file} (not created, {device_vendor} CEF)"
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

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Return configuration schema for CEF auditing plugin."""
        return {
            "enabled": {
                "type": "boolean",
                "label": "Enable CEF audit logging",
                "description": "When enabled, logs all MCP requests and responses in Common Event Format (CEF) for SIEM integration. CEF is an industry-standard format widely accepted by security information and event management systems. When disabled, no CEF logging occurs.",
                "default": True,
                "required": True,
            },
            "output_file": {
                "type": "string",
                "label": "Path to CEF output file",
                "description": "File path where CEF audit logs will be written. Supports relative paths (relative to config directory) and absolute paths. File will be created if it doesn't exist. CEF logs are optimized for SIEM ingestion.",
                "default": "audit.cef",
                "required": True,
            },
            "cef_config": {
                "type": "object",
                "label": "CEF Configuration",
                "description": "Common Event Format specific configuration options for SIEM integration and compliance reporting.",
                "properties": {
                    "device_vendor": {
                        "type": "string",
                        "label": "Device Vendor",
                        "description": "Vendor name in CEF header (appears in all CEF events)",
                        "default": "Gatekit",
                    },
                    "device_product": {
                        "type": "string",
                        "label": "Device Product",
                        "description": "Product name in CEF header (appears in all CEF events)",
                        "default": "MCP Gateway",
                    },
                    "device_version": {
                        "type": "enum",
                        "label": "Device Version",
                        "description": "Version information in CEF header",
                        "options": ["auto", "manual"],
                        "display_labels": {
                            "auto": "Auto-detect Gatekit Version",
                            "manual": "Manual Version String",
                        },
                        "default": "auto",
                    },
                    "device_hostname": {
                        "type": "string",
                        "label": "Device Hostname",
                        "description": "Optional hostname for network correlation (leave empty for auto-detection)",
                        "default": "",
                    },
                    "device_ip": {
                        "type": "string",
                        "label": "Device IP Address",
                        "description": "Optional IP address for network correlation (leave empty for auto-detection)",
                        "default": "",
                    },
                    "compliance_tags": {
                        "type": "list",
                        "label": "Compliance Tags",
                        "description": "List of compliance frameworks for regulatory tracking",
                        "items": {"type": "string"},
                        "default": [],
                    },
                    "risk_scoring": {
                        "type": "boolean",
                        "label": "Enable Risk Scoring",
                        "description": "Include risk assessment metadata in CEF events",
                        "default": True,
                    },
                    "regulatory_fields": {
                        "type": "boolean",
                        "label": "Include Regulatory Fields",
                        "description": "Add regulatory compliance fields to CEF events",
                        "default": True,
                    },
                    "lean_mode": {
                        "type": "boolean",
                        "label": "Lean Mode",
                        "description": "Reduce duplicate fields in CEF output for bandwidth optimization",
                        "default": False,
                    },
                    "drop_args": {
                        "type": "boolean",
                        "label": "Drop Request/Response Arguments",
                        "description": "Exclude detailed request/response content from CEF logs to reduce size and protect sensitive data",
                        "default": False,
                    },
                    "hash_large_fields": {
                        "type": "boolean",
                        "label": "Hash Large Fields",
                        "description": "Replace large content fields with SHA256 hashes to reduce log size while maintaining integrity verification",
                        "default": False,
                    },
                    "max_message_length": {
                        "type": "number",
                        "label": "Maximum Message Length",
                        "description": "Maximum length for CEF messages before truncation (helps prevent log injection)",
                        "default": 50000,
                        "min": 1000,
                        "max": 100000,
                    },
                    "truncation_indicator": {
                        "type": "string",
                        "label": "Truncation Indicator",
                        "description": "String appended to truncated fields",
                        "default": "...[truncated]",
                    },
                    "field_max_lengths": {
                        "type": "object",
                        "label": "Field Length Limits",
                        "description": "Maximum lengths for specific CEF fields to prevent oversized logs",
                        "properties": {
                            "reason": {
                                "type": "number",
                                "label": "Reason Field Max Length",
                                "default": 2000,
                            },
                            "tool": {
                                "type": "number",
                                "label": "Tool Field Max Length",
                                "default": 256,
                            },
                            "method": {
                                "type": "number",
                                "label": "Method Field Max Length",
                                "default": 256,
                            },
                            "plugin": {
                                "type": "number",
                                "label": "Plugin Field Max Length",
                                "default": 256,
                            },
                            "server_name": {
                                "type": "number",
                                "label": "Server Name Field Max Length",
                                "default": 256,
                            },
                            "args": {
                                "type": "number",
                                "label": "Arguments Field Max Length",
                                "default": 10000,
                            },
                            "message": {
                                "type": "number",
                                "label": "Message Field Max Length",
                                "default": 10000,
                            },
                            "default": {
                                "type": "number",
                                "label": "Default Field Max Length",
                                "default": 1000,
                            },
                        },
                    },
                },
            },
        }

    # Type annotations for class attributes
    device_vendor: str
    device_product: str
    device_version: str
    cef_version: str
    compliance_tags: List[str]
    risk_scoring: bool
    regulatory_fields: bool
    lean_mode: bool
    field_max_lengths: Dict[str, int]
    truncation_indicator: str
    drop_args: bool
    hash_large_fields: bool
    device_hostname: Optional[str]
    device_ip: Optional[str]

    def __init__(self, config: Dict[str, Any]):
        """Initialize CEF auditing plugin with configuration.

        Args:
            config: Plugin configuration dictionary with CEF-specific options:
                   - device_vendor: Vendor name (default: "Gatekit")
                   - device_product: Product name (default: "MCP Gateway")
                   - device_version: Version string (default: auto-detected)
                   - compliance_tags: List of compliance frameworks
                   - risk_scoring: Enable risk scoring (default: True)
                   - regulatory_fields: Include regulatory fields (default: True)
                   Plus all BaseAuditingPlugin options (output_file, etc.)

        Raises:
            ValueError: If configuration is invalid
            TypeError: If configuration has wrong types
        """
        # Initialize base class first
        super().__init__(config)

        # CEF-specific configuration - ALL from cef_config section
        cef_config = config.get("cef_config", {})

        # Device identification
        device_version = cef_config.get("device_version")
        if device_version == "auto":
            device_version = None  # Will use automatic detection

        self.device_vendor = cef_config.get("device_vendor", "Gatekit")
        self.device_product = cef_config.get("device_product", "MCP Gateway")
        self.device_version = device_version or get_gatekit_version()
        self.cef_version = "0"

        # Optional device fields for network correlation
        self.device_hostname = cef_config.get("device_hostname")
        self.device_ip = cef_config.get("device_ip")

        # Compliance Extensions
        self.compliance_tags = cef_config.get("compliance_tags", [])
        self.risk_scoring = cef_config.get("risk_scoring", True)
        self.regulatory_fields = cef_config.get("regulatory_fields", True)

        # Performance and privacy options
        self.lean_mode = cef_config.get("lean_mode", False)
        self.drop_args = cef_config.get("drop_args", False)
        self.hash_large_fields = cef_config.get("hash_large_fields", False)

        # Field length limits for sanitization
        self.field_max_lengths = cef_config.get(
            "field_max_lengths",
            {
                "reason": 2000,
                "tool": 256,
                "method": 256,
                "plugin": 256,
                "server_name": 256,
                "device_hostname": 256,
                "device_ip": 50,
                "source_ip": 50,
                "destination_ip": 50,
                "args": 10000,
                "message": 10000,
                "default": 1000,
            },
        )
        self.truncation_indicator = cef_config.get(
            "truncation_indicator", "...[truncated]"
        )

        # Set high max_message_length to avoid double truncation
        self.max_message_length = cef_config.get("max_message_length", 50000)

        # Validate CEF configuration
        if not isinstance(self.device_vendor, str) or not self.device_vendor.strip():
            raise ValueError("device_vendor must be a non-empty string")

        if not isinstance(self.device_product, str) or not self.device_product.strip():
            raise ValueError("device_product must be a non-empty string")

        if not isinstance(self.device_version, str) or not self.device_version.strip():
            raise ValueError("device_version must be a non-empty string")

        if not isinstance(self.compliance_tags, list):
            raise ValueError("compliance_tags must be a list")

    def _sanitize_for_log(
        self, value: Optional[str], field_name: str = "default"
    ) -> str:
        """Centralized sanitization - apply BEFORE CEF escaping.

        - Remove control characters
        - Apply configurable per-field length limits
        - Prevent log injection
        - Avoid double-escaping by sanitizing first
        """
        if value is None:
            return ""

        value = str(value)  # Ensure string type

        # Remove control characters except tab/newline
        sanitized = "".join(
            char for char in value if char.isprintable() or char in "\t\n"
        )

        # Replace newlines with escaped version
        sanitized = sanitized.replace("\n", "\\n").replace("\r", "\\r")

        # Apply field-specific length limit from config
        max_length = self.field_max_lengths.get(
            field_name, self.field_max_lengths["default"]
        )

        if len(sanitized) > max_length:
            # Use stored truncation_indicator
            sanitized = (
                sanitized[: max_length - len(self.truncation_indicator)]
                + self.truncation_indicator
            )

        return sanitized

    def _format_request_entry(self, data: Dict[str, Any]) -> str:
        """Format extracted request data into CEF log entry.

        Args:
            data: Dictionary containing extracted request data

        Returns:
            str: CEF-formatted log message
        """
        # Use event type from extracted data, but check for CEF-specific modifications
        event_type = data["event_type"]

        # CEF uses different names for some event types
        if event_type == "REQUEST_MODIFIED":
            # Check for redaction hint in reason
            if data["reason"] and "redact" in data["reason"].lower():
                event_type = "REDACTION"
            else:
                event_type = "MODIFICATION"

        # Sanitize all user-controlled fields
        sanitized_reason = self._sanitize_for_log(data["reason"], "reason")
        sanitized_method = self._sanitize_for_log(data.get("method", ""), "method")
        sanitized_tool = None
        if "tool_name" in data:
            sanitized_tool = self._sanitize_for_log(data["tool_name"], "tool")
        elif event_type == "SECURITY_BLOCK" and data.get("method") == "tools/call":
            sanitized_tool = "unknown"

        sanitized_server = self._sanitize_for_log(data["server_name"], "server_name")
        sanitized_plugin = self._sanitize_for_log(data["plugin_name"], "plugin")

        # Build event data with sanitized values
        event_data = {
            "event_type": event_type,
            "timestamp": data["timestamp"],
            "method": sanitized_method,
            "request_id": data.get("request_id"),
            "status": "ALLOWED" if data["is_allowed"] else "BLOCKED",
        }

        if sanitized_tool:
            event_data["tool"] = sanitized_tool

        if sanitized_plugin != "unknown":
            event_data["plugin"] = sanitized_plugin

        if sanitized_reason:
            event_data["reason"] = sanitized_reason

        # Add request arguments if not dropped
        if not self.drop_args and "params" in data and data["params"]:
            event_data["args"] = data["params"]

        event_data["server_name"] = sanitized_server

        return self._format_cef_message(event_data)

    def _format_response_entry(self, data: Dict[str, Any]) -> str:
        """Format extracted response data into CEF log entry.

        Args:
            data: Dictionary containing extracted response data

        Returns:
            str: CEF-formatted log message
        """
        # Use event type from extracted data, handle CEF-specific naming
        event_type = data["event_type"]

        # CEF uses different names for some event types
        if event_type == "RESPONSE_MODIFIED":
            # Check for specific modification types
            if data.get("method") == "tools/list":
                event_type = "TOOLS_FILTERED"
            elif data["reason"] and "redact" in data["reason"].lower():
                event_type = "REDACTION"
            else:
                event_type = "MODIFICATION"
        elif data.get("response_status") == "error":
            # Classify error type
            error_code = data.get("error_code", 0)
            if isinstance(error_code, int) and error_code < -32000:
                event_type = "UPSTREAM_ERROR"
            else:
                event_type = "ERROR"

        # Sanitize all user-controlled fields
        sanitized_reason = self._sanitize_for_log(data["reason"], "reason")
        sanitized_plugin = self._sanitize_for_log(data["plugin_name"], "plugin")
        sanitized_server = self._sanitize_for_log(data["server_name"], "server_name")

        # Build event data with sanitized values
        event_data = {
            "event_type": event_type,
            "timestamp": data["timestamp"],
            "request_id": data.get("request_id"),
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

        if sanitized_plugin != "unknown":
            event_data["plugin"] = sanitized_plugin

        if sanitized_reason:
            event_data["reason"] = sanitized_reason

        # Add duration if available
        if "duration_ms" in data:
            event_data["duration_ms"] = data["duration_ms"]

        # Add error info if present
        if not self.drop_args and "error_code" in data:
            event_data["args"] = {
                "code": data["error_code"],
                "message": data.get("error_message", ""),
            }

        event_data["server_name"] = sanitized_server

        return self._format_cef_message(event_data)

    def _format_notification_entry(self, data: Dict[str, Any]) -> str:
        """Format extracted notification data into CEF log entry.

        Args:
            data: Dictionary containing extracted notification data

        Returns:
            str: CEF-formatted log message
        """
        # Sanitize all user-controlled fields
        sanitized_method = self._sanitize_for_log(data.get("method", ""), "method")
        sanitized_reason = self._sanitize_for_log(data["reason"], "reason")
        sanitized_plugin = self._sanitize_for_log(data["plugin_name"], "plugin")
        sanitized_server = self._sanitize_for_log(data["server_name"], "server_name")

        # Build event data with sanitized values
        event_data = {
            "event_type": "NOTIFICATION",
            "timestamp": data["timestamp"],
            "method": sanitized_method,
            "status": "NOTIFICATION",
        }

        if sanitized_plugin != "unknown":
            event_data["plugin"] = sanitized_plugin

        if sanitized_reason:
            event_data["reason"] = sanitized_reason

        event_data["server_name"] = sanitized_server

        return self._format_cef_message(event_data)

    def _format_cef_message(self, event_data: Dict[str, Any]) -> str:
        """Format Gatekit event as CEF message.

        Args:
            event_data: Event data dictionary from Gatekit

        Returns:
            str: Formatted CEF message
        """
        # Get event mapping
        event_type = event_data.get("event_type", "UNKNOWN")
        event_mapping = CEF_EVENT_MAPPINGS.get(event_type, DEFAULT_CEF_EVENT_MAPPING)

        # Build CEF header
        header_parts = [
            f"CEF:{self.cef_version}",
            self._escape_cef_header(self.device_vendor),
            self._escape_cef_header(self.device_product),
            self._escape_cef_header(self.device_version),
            self._escape_cef_header(event_mapping["event_id"]),
            self._escape_cef_header(event_mapping["name"]),
            self._escape_cef_header(str(event_mapping["severity"])),
        ]

        # Build extension fields
        extensions = []

        # Required fields
        if "timestamp" in event_data:
            cef_timestamp = self._convert_to_cef_timestamp(event_data["timestamp"])
            extensions.append(f"rt={self._escape_cef_extension(cef_timestamp)}")

        if "request_id" in event_data:
            extensions.append(
                f"requestId={self._escape_cef_extension(str(event_data['request_id']))}"
            )

        # Action based on status - ALWAYS normalize to lowercase
        status = event_data.get("status", "")
        if status:
            normalized_status = str(status).lower()
            extensions.append(f"act={self._escape_cef_extension(normalized_status)}")

        # Optional fields using CEF custom strings
        if "reason" in event_data:
            extensions.append(
                f"reason={self._escape_cef_extension(event_data['reason'])}"
            )

        if "plugin" in event_data:
            extensions.append(f"cs1={self._escape_cef_extension(event_data['plugin'])}")
            extensions.append("cs1Label=Plugin")
            # Only add duplicate standard field if not in lean mode
            if not self.lean_mode:
                extensions.append(
                    f"sourceUserName={self._escape_cef_extension(event_data['plugin'])}"
                )

        if "method" in event_data:
            extensions.append(f"cs2={self._escape_cef_extension(event_data['method'])}")
            extensions.append("cs2Label=Method")
            if not self.lean_mode:
                extensions.append(
                    f"requestMethod={self._escape_cef_extension(event_data['method'])}"
                )

        if "tool" in event_data:
            extensions.append(f"cs3={self._escape_cef_extension(event_data['tool'])}")
            extensions.append("cs3Label=Tool")
            if not self.lean_mode:
                extensions.append(
                    f"fileName={self._escape_cef_extension(event_data['tool'])}"
                )

        if "duration_ms" in event_data:
            extensions.append(
                f"cs4={self._escape_cef_extension(str(event_data['duration_ms']))}"
            )
            extensions.append("cs4Label=Duration")
            if not self.lean_mode:
                extensions.append(
                    f"duration={self._escape_cef_extension(str(event_data['duration_ms']))}"
                )

        if "server_name" in event_data:
            extensions.append(
                f"cs5={self._escape_cef_extension(event_data['server_name'])}"
            )
            extensions.append("cs5Label=Server")
            if not self.lean_mode:
                extensions.append(
                    f"destinationServiceName={self._escape_cef_extension(event_data['server_name'])}"
                )

        # Additional standard CEF fields
        if "user" in event_data:
            extensions.append(
                f"duser={self._escape_cef_extension(str(event_data['user']))}"
            )

        if "args" in event_data and not self.drop_args:
            args_str = str(event_data["args"]) if event_data["args"] is not None else ""
            if self.hash_large_fields and len(args_str) > self.field_max_lengths.get(
                "args", 10000
            ):
                import hashlib

                hash_val = hashlib.sha256(args_str.encode()).hexdigest()[:16]
                extensions.append(
                    f"msg=[SHA256:{hash_val}...{self.truncation_indicator}]"
                )
            else:
                sanitized_args = self._sanitize_for_log(args_str, "args")
                extensions.append(f"msg={self._escape_cef_extension(sanitized_args)}")

        # Compliance Extensions
        if self.compliance_tags:
            compliance_str = ",".join(self.compliance_tags)
            extensions.append(f"cs6={self._escape_cef_extension(compliance_str)}")
            extensions.append("cs6Label=Compliance")

        # Network fields - NO misleading defaults!
        source_ip = event_data.get("source_ip")
        destination_ip = event_data.get("destination_ip")

        # Only add if actually known (sanitize first!)
        if source_ip is not None:
            sanitized_src = self._sanitize_for_log(str(source_ip), "source_ip")
            extensions.append(f"src={self._escape_cef_extension(sanitized_src)}")

        if destination_ip is not None:
            sanitized_dst = self._sanitize_for_log(
                str(destination_ip), "destination_ip"
            )
            extensions.append(f"dst={self._escape_cef_extension(sanitized_dst)}")

        # Add device fields only if configured (ALWAYS sanitize first!)
        if self.device_hostname:
            sanitized_hostname = self._sanitize_for_log(
                self.device_hostname, "device_hostname"
            )
            extensions.append(
                f"dvchost={self._escape_cef_extension(sanitized_hostname)}"
            )

        if self.device_ip:
            sanitized_ip = self._sanitize_for_log(self.device_ip, "device_ip")
            extensions.append(f"dvc={self._escape_cef_extension(sanitized_ip)}")
        # NEVER default to 127.0.0.1 or 'gatekit' - omit if unknown

        # Combine header and extensions
        header = "|".join(header_parts)
        extension = " ".join(extensions)

        return f"{header}|{extension}"

    def _escape_cef_header(self, value: str) -> str:
        """Escape header field values (pipe and backslash).

        Args:
            value: Value to escape

        Returns:
            str: Escaped value
        """
        return str(value).replace("\\", "\\\\").replace("|", "\\|")

    def _escape_cef_extension(self, value: str) -> str:
        """Escape extension field values (backslash, equals, newlines, pipes).

        Args:
            value: Value to escape

        Returns:
            str: Escaped value
        """
        return (
            str(value)
            .replace("\\", "\\\\")
            .replace("=", "\\=")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("|", "\\|")
        )

    def _convert_to_cef_timestamp(self, timestamp: str) -> str:
        """Convert ISO timestamp to CEF format with UTC normalization.

        Args:
            timestamp: ISO timestamp string (any timezone)

        Returns:
            str: CEF timestamp in UTC (MMM dd yyyy HH:mm:ss)
        """
        try:
            from datetime import datetime, timezone

            # Parse ISO timestamp with timezone awareness
            if timestamp.endswith("Z"):
                dt = datetime.fromisoformat(timestamp[:-1]).replace(tzinfo=timezone.utc)
            elif "+" in timestamp or timestamp.count("-") > 2:
                # Has timezone offset
                dt = datetime.fromisoformat(timestamp)
            else:
                # No timezone, assume UTC
                dt = datetime.fromisoformat(timestamp).replace(tzinfo=timezone.utc)

            # Normalize to UTC
            dt_utc = dt.astimezone(timezone.utc)

            # Format for CEF (human-readable UTC)
            # Document: All CEF timestamps are normalized to UTC
            return dt_utc.strftime("%b %d %Y %H:%M:%S")

        except Exception as e:
            # Log warning about timestamp parse failure (ensure logger exists)
            if hasattr(self, "logger") and self.logger:
                self.logger.warning(f"Failed to parse timestamp {timestamp}: {e}")
            # Return original on failure
            return timestamp


# Policy manifest for policy-based plugin discovery
POLICIES = {"cef_auditing": CefAuditingPlugin}
