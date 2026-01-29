"""Syslog auditing plugin for Gatekit MCP gateway.

This module provides the SyslogAuditingPlugin class that logs MCP requests and responses
in RFC 5424 or RFC 3164 syslog format with support for multiple transport methods
including TLS for secure network delivery and real-time compliance monitoring.
"""

import asyncio
import os
import socket
import ssl
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import re
from gatekit.plugins.auditing.base import BaseAuditingPlugin

# Precompiled regex patterns for performance
CONTROL_CHARS = re.compile(r"[\x00-\x1F\x7F]")
MULTIPLE_SPACES = re.compile(r" +")


class SyslogAuditingPlugin(BaseAuditingPlugin):
    """Syslog auditing plugin with TLS transport support.

    Logs MCP requests and responses in syslog format for centralized logging
    and SIEM integration. Supports both file-based logging and network transport
    with TLS encryption for secure real-time monitoring.

    Features:
    - RFC 5424 and RFC 3164 syslog format support
    - Multiple transport methods: file, UDP, TCP, TLS
    - TLS encryption with certificate verification
    - Real-time monitoring capabilities
    - Centralized logging system integration
    - Configurable facility and severity levels
    """

    # TUI Display Metadata
    DISPLAY_NAME = "Syslog"

    @classmethod
    def describe_status(cls, config: Dict[str, Any]) -> str:
        """Generate status description from syslog configuration."""
        if not config or not config.get("enabled", False):
            return "Export audit logs to syslog format"

        syslog_config = config.get("syslog_config", {})
        transport = syslog_config.get("transport", "file")
        rfc_format = syslog_config.get("rfc_format", "5424")

        if transport == "file":
            output_file = config.get("output_file", "audit.log")
            return f"{output_file} (RFC {rfc_format})"
        else:
            remote_host = syslog_config.get("remote_host", "unknown")
            remote_port = syslog_config.get("remote_port", 514)
            transport_upper = transport.upper()
            return f"{remote_host}:{remote_port} ({transport_upper}, RFC {rfc_format})"

    @classmethod
    def get_display_actions(cls, config: Dict[str, Any]) -> List[str]:
        """Return actions based on configuration state."""
        if config and config.get("enabled", False):
            syslog_config = config.get("syslog_config", {})
            if syslog_config.get("transport", "file") == "file":
                output_file = config.get("output_file", "")
                try:
                    import os

                    if output_file and os.path.exists(output_file):
                        return ["View Logs", "Configure"]
                except:
                    pass
            return ["Configure"]
        return ["Setup"]

    # Type annotations for class attributes
    rfc_format: str
    facility: int
    hostname: str
    app_name: str
    process_id: str
    transport: str
    remote_host: Optional[str]
    remote_port: int
    tls_verify: bool
    tls_cert_file: Optional[str]
    tls_key_file: Optional[str]
    tls_ca_file: Optional[str]
    sd_field_max_length: int
    msg_max_length: int
    truncation_marker: str
    _ssl_context: Optional[ssl.SSLContext]
    _tls_warning_logged: bool

    def __init__(self, config: Dict[str, Any]):
        """Initialize Syslog auditing plugin with configuration.

        Args:
            config: Plugin configuration dictionary with syslog-specific options:
                   - syslog_config: Dictionary containing:
                     - rfc_format: "5424" or "3164" (default: "5424")
                     - facility: Syslog facility code (default: 16 = local0)
                     - transport: "file", "udp", "tcp", "tls" (default: "file")
                       Note: Network transports (especially TLS) are experimental in v0.1.0
                     - remote_host: Remote syslog server hostname (required for network transports)
                     - remote_port: Remote syslog server port (default: 514 for UDP/TCP, 6514 for TLS)
                     - tls_verify: Verify TLS certificates (default: True)
                     - tls_cert_file: Path to client certificate file
                     - tls_key_file: Path to client key file
                     - tls_ca_file: Path to CA certificate file
                   Plus all BaseAuditingPlugin options (output_file, etc.)

        Raises:
            ValueError: If configuration is invalid
            TypeError: If configuration has wrong types
        """
        # Initialize base class first
        super().__init__(config)

        # Syslog-specific configuration
        syslog_config = config.get("syslog_config", {})
        self.rfc_format = syslog_config.get("rfc_format", "5424")
        self.facility = syslog_config.get("facility", 16)  # local0
        self.hostname = socket.gethostname()
        self.app_name = "gatekit"
        self.process_id = str(os.getpid())

        # Transport configuration
        self.transport = syslog_config.get("transport", "file")
        self.remote_host = syslog_config.get("remote_host")
        self.remote_port = syslog_config.get("remote_port")

        # Set default port based on transport if not specified
        if self.remote_port is None:
            if self.transport == "tls":
                self.remote_port = 6514  # Standard TLS syslog port
            else:
                self.remote_port = 514  # Standard UDP/TCP syslog port

        # TLS configuration
        self.tls_verify = syslog_config.get("tls_verify", True)
        self.tls_cert_file = syslog_config.get("tls_cert_file")
        self.tls_key_file = syslog_config.get("tls_key_file")
        self.tls_ca_file = syslog_config.get("tls_ca_file")

        # Configurable length limits and truncation
        self.sd_field_max_length = syslog_config.get("sd_field_max_length", 256)
        self.msg_max_length = syslog_config.get("msg_max_length", 2048)
        self.truncation_marker = syslog_config.get("truncation_marker", "...")

        # Validate configuration
        self._validate_config()

        # Cache computed constants for performance
        self._cached_hostname = self.hostname
        self._cached_process_id = self.process_id

        # Initialize SSL context and warning tracking
        self._ssl_context = None
        self._tls_warning_logged = False
        if self.transport in ["udp", "tcp", "tls"]:
            self._setup_network_transport()

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Return configuration schema for Syslog auditing plugin."""
        return {
            "enabled": {
                "type": "boolean",
                "label": "Enable syslog audit logging",
                "description": "When enabled, logs all MCP communications in standard syslog format for centralized logging and SIEM integration. Supports both file output and network transports including secure TLS delivery.",
                "default": True,
                "required": True,
            },
            "output_file": {
                "type": "string",
                "label": "Path to syslog output file",
                "description": "File path where syslog audit logs will be written. Supports relative paths (relative to config directory) and absolute paths. File will be created if it doesn't exist. Used for file transport or as backup for network transports.",
                "default": "audit.log",
                "required": True,
            },
            "syslog_config": {
                "type": "object",
                "label": "Syslog Configuration",
                "description": "RFC-compliant syslog configuration options for format, transport, and network delivery settings.",
                "properties": {
                    "rfc_format": {
                        "type": "enum",
                        "label": "RFC Format",
                        "description": "Syslog message format standard. RFC 5424 provides structured data support, while RFC 3164 offers legacy compatibility.",
                        "options": ["5424", "3164"],
                        "display_labels": {
                            "5424": "RFC 5424 (Modern, Structured)",
                            "3164": "RFC 3164 (Legacy, Compatible)",
                        },
                        "default": "5424",
                    },
                    "facility": {
                        "type": "number",
                        "label": "Syslog Facility Code (0-23)",
                        "description": "Standard syslog facility code. Common values: 16 (local0), 17 (local1), 18 (local2). See RFC 5424 for complete facility list.",
                        "default": 16,
                        "min": 0,
                        "max": 23,
                    },
                    "transport": {
                        "type": "enum",
                        "label": "Transport Method",
                        "description": "Delivery method for syslog messages. File: local file output. UDP: standard syslog over UDP. TCP: reliable delivery over TCP. TLS: secure encrypted delivery.",
                        "options": ["file", "udp", "tcp", "tls"],
                        "display_labels": {
                            "file": "File Output",
                            "udp": "UDP (Standard)",
                            "tcp": "TCP (Reliable)",
                            "tls": "TLS (Secure)",
                        },
                        "default": "file",
                    },
                    "remote_host": {
                        "type": "string",
                        "label": "Remote Syslog Server",
                        "description": "Hostname or IP address of remote syslog server (required for UDP/TCP/TLS transports)",
                        "default": "",
                    },
                    "remote_port": {
                        "type": "number",
                        "label": "Remote Syslog Port",
                        "description": "Port number for remote syslog server. Standard ports: 514 (UDP/TCP), 6514 (TLS)",
                        "default": 514,
                        "min": 1,
                        "max": 65535,
                    },
                    "tls_verify": {
                        "type": "boolean",
                        "label": "Verify TLS Certificates",
                        "description": "Enable certificate verification for TLS transport (recommended for security)",
                        "default": True,
                    },
                    "tls_cert_file": {
                        "type": "string",
                        "label": "Client Certificate File",
                        "description": "Path to client certificate file for TLS mutual authentication (optional)",
                        "default": "",
                    },
                    "tls_key_file": {
                        "type": "string",
                        "label": "Client Key File",
                        "description": "Path to client private key file for TLS mutual authentication (optional)",
                        "default": "",
                    },
                    "tls_ca_file": {
                        "type": "string",
                        "label": "CA Certificate File",
                        "description": "Path to CA certificate file for TLS server verification (optional)",
                        "default": "",
                    },
                    "sd_field_max_length": {
                        "type": "number",
                        "label": "Structured Data Field Max Length",
                        "description": "Maximum length for individual structured data fields (RFC 5424 only)",
                        "default": 256,
                        "min": 50,
                        "max": 2048,
                    },
                    "msg_max_length": {
                        "type": "number",
                        "label": "Message Max Length",
                        "description": "Maximum length for syslog message content before truncation",
                        "default": 2048,
                        "min": 100,
                        "max": 8192,
                    },
                    "truncation_marker": {
                        "type": "string",
                        "label": "Truncation Marker",
                        "description": "Text marker used to indicate when content has been truncated",
                        "default": "...",
                    },
                },
            },
            "critical": {
                "type": "boolean",
                "label": "Critical Plugin",
                "description": "If enabled, plugin failures will halt MCP processing. If disabled, errors are logged but processing continues.",
                "default": False,
            },
        }

    def _validate_config(self):
        """Validate syslog configuration."""
        if self.rfc_format not in ["5424", "3164"]:
            raise ValueError(
                f"Invalid rfc_format '{self.rfc_format}'. Must be '5424' or '3164'"
            )

        if (
            not isinstance(self.facility, int)
            or self.facility < 0
            or self.facility > 23
        ):
            raise ValueError(
                f"Invalid facility {self.facility}. Must be between 0 and 23"
            )

        if self.transport not in ["file", "udp", "tcp", "tls"]:
            raise ValueError(
                f"Invalid transport '{self.transport}'. Must be one of: file, udp, tcp, tls"
            )

        if self.transport in ["udp", "tcp", "tls"] and not self.remote_host:
            raise ValueError(
                f"remote_host is required for transport '{self.transport}'"
            )

        if (
            not isinstance(self.remote_port, int)
            or self.remote_port <= 0
            or self.remote_port > 65535
        ):
            raise ValueError(
                f"Invalid remote_port {self.remote_port}. Must be between 1 and 65535"
            )

        # Validate length limits with dynamic marker computation
        if not isinstance(
            self.sd_field_max_length, int
        ) or self.sd_field_max_length <= len(self.truncation_marker):
            raise ValueError(
                f"sd_field_max_length must be integer > {len(self.truncation_marker)}"
            )

        msg_marker_len = len(
            f" ({self.truncation_marker})"
        )  # Match runtime marker format
        if (
            not isinstance(self.msg_max_length, int)
            or self.msg_max_length <= msg_marker_len
        ):
            raise ValueError(f"msg_max_length must be integer > {msg_marker_len}")

        # Validate TLS configuration
        if self.transport == "tls":
            if self.tls_cert_file and not isinstance(self.tls_cert_file, str):
                raise ValueError("tls_cert_file must be a string path")
            if self.tls_key_file and not isinstance(self.tls_key_file, str):
                raise ValueError("tls_key_file must be a string path")
            if self.tls_ca_file and not isinstance(self.tls_ca_file, str):
                raise ValueError("tls_ca_file must be a string path")

    def _setup_network_transport(self):
        """Set up network transport for syslog delivery.

        Note: Network transports (especially TLS) are experimental in v0.1.0
        and may have issues with connection pooling and retry logic.
        """
        if self.transport == "tls":
            # Set up SSL context for TLS transport
            self._ssl_context = ssl.create_default_context()

            if not self.tls_verify:
                # One-time warning to avoid log spam on frequent instantiation
                if not self._tls_warning_logged:
                    import logging

                    logger = logging.getLogger(f"gatekit.audit.{id(self)}")
                    logger.warning(
                        "TLS certificate verification is DISABLED for syslog transport - this reduces security"
                    )
                    self._tls_warning_logged = True
                self._ssl_context.check_hostname = False
                self._ssl_context.verify_mode = ssl.CERT_NONE

            if self.tls_cert_file and self.tls_key_file:
                self._ssl_context.load_cert_chain(self.tls_cert_file, self.tls_key_file)

            if self.tls_ca_file:
                self._ssl_context.load_verify_locations(self.tls_ca_file)

    async def _send_via_network(self, message: str):
        """Send syslog message via network transport.

        Args:
            message: Formatted syslog message to send
        """
        try:
            if self.transport == "udp":
                await self._send_udp(message)
            elif self.transport == "tcp":
                await self._send_tcp(message)
            elif self.transport == "tls":
                await self._send_tls(message)
        except Exception as e:
            # If network sending fails, fall back to base class file logging
            import logging

            logger = logging.getLogger(f"gatekit.audit.{id(self)}")
            logger.exception(f"Failed to send syslog message via {self.transport}: {e}")

            if self.critical:
                raise RuntimeError(
                    f"Critical syslog auditing plugin failed to send message: {e}"
                )
            # For non-critical plugins, the message is already written to file by base class

    async def _send_udp(self, message: str):
        """Send syslog message via UDP."""
        # Create UDP socket and send asynchronously
        loop = asyncio.get_running_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setblocking(False)
            await loop.sock_sendto(
                sock, message.encode("utf-8"), (self.remote_host, self.remote_port)
            )
        finally:
            sock.close()

    async def _send_tcp(self, message: str):
        """Send syslog message via TCP."""
        reader, writer = await asyncio.open_connection(
            self.remote_host, self.remote_port
        )
        try:
            # RFC 6587 - TCP transport with octet counting
            message_bytes = message.encode("utf-8")
            framed_message = f"{len(message_bytes)} ".encode("utf-8") + message_bytes
            writer.write(framed_message)
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def _send_tls(self, message: str):
        """Send syslog message via TLS."""
        reader, writer = await asyncio.open_connection(
            self.remote_host, self.remote_port, ssl=self._ssl_context
        )
        try:
            # RFC 5425 - TLS transport with octet counting
            message_bytes = message.encode("utf-8")
            framed_message = f"{len(message_bytes)} ".encode("utf-8") + message_bytes
            writer.write(framed_message)
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    def _format_request_entry(self, data: Dict[str, Any]) -> str:
        """Format extracted request data into syslog log entry.

        Args:
            data: Dictionary containing extracted request data

        Returns:
            str: Syslog-formatted log message
        """
        # Determine event type and severity from extracted data
        event_type = data["event_type"]
        if event_type == "SECURITY_BLOCK":
            severity = 4  # Warning
        elif event_type == "TOOLS_FILTERED":
            severity = 5  # Notice
        elif event_type == "REQUEST_MODIFIED":
            severity = 5  # Notice
            event_type = "MODIFICATION"  # Syslog uses different naming
        else:
            severity = 6  # Informational
            event_type = "REQUEST"

        # Build structured data using extracted info
        structured_data = self._build_structured_data_from_dict(data, event_type)

        # Create message content
        message_content = f"Gatekit MCP {event_type}: {data.get('method', '')}"
        if "tool_name" in data:
            message_content += f" - {data['tool_name']}"

        if not data["is_allowed"]:
            message_content += f" - BLOCKED: {data['reason']}"
        elif data["reason"]:
            message_content += f" - {data['reason']}"

        # Sanitize message content
        message_content = self._sanitize_message_content(message_content)
        return self._format_syslog_message(
            severity, structured_data, message_content, event_type
        )

    def _format_response_entry(self, data: Dict[str, Any]) -> str:
        """Format extracted response data into syslog log entry.

        Args:
            data: Dictionary containing extracted response data

        Returns:
            str: Syslog-formatted log message
        """
        # Determine event type and severity from extracted data
        event_type = data["event_type"]
        if event_type == "SECURITY_BLOCK":
            severity = 4  # Warning
        elif event_type in ["ERROR", "UPSTREAM_ERROR"]:
            severity = 3  # Error
        elif event_type == "RESPONSE_MODIFIED":
            severity = 5  # Notice
            event_type = "REDACTION"  # Syslog uses different naming
        else:
            severity = 6  # Informational
            event_type = "RESPONSE"

        # Build structured data using extracted info
        structured_data = self._build_structured_data_from_dict(data, event_type)

        # Create message content
        message_content = f"Gatekit MCP {event_type}: response"
        if "error_message" in data:
            message_content += f" - ERROR: {data['error_message']}"
        elif data["reason"]:
            message_content += f" - {data['reason']}"

        # Add duration if available
        if "duration_ms" in data:
            duration_s = data["duration_ms"] / 1000
            message_content += f" (duration: {duration_s:.3f}s)"

        # Sanitize message content
        message_content = self._sanitize_message_content(message_content)
        return self._format_syslog_message(
            severity, structured_data, message_content, event_type
        )

    def _format_notification_entry(self, data: Dict[str, Any]) -> str:
        """Format extracted notification data into syslog log entry.

        Args:
            data: Dictionary containing extracted notification data

        Returns:
            str: Syslog-formatted log message
        """
        severity = 6  # Informational
        event_type = "NOTIFICATION"

        # Build structured data using extracted info
        structured_data = self._build_structured_data_from_dict(data, event_type)

        # Create message content
        message_content = f"Gatekit MCP {event_type}: {data.get('method', '')}"
        if data["reason"]:
            message_content += f" - {data['reason']}"

        # Sanitize message content
        message_content = self._sanitize_message_content(message_content)
        return self._format_syslog_message(
            severity, structured_data, message_content, event_type
        )

    def _build_structured_data_from_dict(
        self, data: Dict[str, Any], event_type: str
    ) -> str:
        """Build RFC 5424 structured data section from extracted data.

        Args:
            data: Dictionary containing extracted data
            event_type: Type of event

        Returns:
            str: Structured data section
        """
        if self.rfc_format != "5424":
            return ""  # RFC 3164 doesn't support structured data

        # Build structured data elements
        sd_elements = []

        # Gatekit enterprise ID and basic event data
        gatekit_data = [
            f'event_type="{self._escape_structured_data(event_type)}"',
            f'status="{self._escape_structured_data("ALLOWED" if data.get("is_allowed", True) else "BLOCKED")}"',
        ]

        if "method" in data:
            gatekit_data.append(
                f'method="{self._escape_structured_data(data["method"])}"'
            )

        if "request_id" in data and data["request_id"]:
            gatekit_data.append(
                f'request_id="{self._escape_structured_data(str(data["request_id"]))}"'
            )

        if "tool_name" in data:
            gatekit_data.append(
                f'tool="{self._escape_structured_data(data["tool_name"])}"'
            )

        if data.get("reason"):
            gatekit_data.append(
                f'reason="{self._escape_structured_data(data["reason"])}"'
            )

        if data.get("plugin_name") and data["plugin_name"] != "unknown":
            gatekit_data.append(
                f'plugin="{self._escape_structured_data(data["plugin_name"])}"'
            )

        gatekit_data.append(
            f'server="{self._escape_structured_data(data["server_name"])}"'
        )

        if "duration_ms" in data:
            gatekit_data.append(f'duration_ms="{data["duration_ms"]}"')

        sd_elements.append(f"[gatekit@32473 {' '.join(gatekit_data)}]")

        return "".join(sd_elements)

    def _escape_structured_data(self, value: str) -> str:
        """Escape structured data values according to RFC 5424 and sanitize control chars.

        Truncates individual structured data fields with plain marker (e.g., "...")
        to maintain clean key=value format in structured data elements.

        Args:
            value: Value to escape

        Returns:
            str: Escaped and sanitized value
        """
        # First sanitize control characters, then escape RFC 5424 special chars
        sanitized = CONTROL_CHARS.sub(" ", value)
        # Collapse multiple spaces
        sanitized = MULTIPLE_SPACES.sub(" ", sanitized).strip()

        # Truncate individual field if too long
        if len(sanitized) > self.sd_field_max_length:
            truncate_at = self.sd_field_max_length - len(self.truncation_marker)
            if truncate_at > 0:  # Guard against negative truncation
                sanitized = sanitized[:truncate_at] + self.truncation_marker
            else:
                sanitized = self.truncation_marker[: self.sd_field_max_length]

        return sanitized.replace("\\", "\\\\").replace('"', '\\"').replace("]", "\\]")

    def _sanitize_message_content(self, content: str) -> str:
        """Sanitize message content by replacing control characters and enforcing size limits.

        Truncates message content with parenthetical marker (e.g., " (...)")
        to clearly indicate truncation in the human-readable message portion.

        Args:
            content: Message content to sanitize

        Returns:
            str: Sanitized content with control characters replaced by spaces and size limited
        """
        # Replace newlines, tabs, and other control characters with spaces
        sanitized = CONTROL_CHARS.sub(" ", content)
        # Collapse multiple spaces
        sanitized = MULTIPLE_SPACES.sub(" ", sanitized).strip()

        # Truncate if too long, using harmonized truncation marker
        if len(sanitized) > self.msg_max_length:
            full_marker = f" ({self.truncation_marker})"
            truncate_at = self.msg_max_length - len(full_marker)
            if truncate_at > 0:  # Guard against negative truncation
                sanitized = sanitized[:truncate_at] + full_marker
            else:
                sanitized = full_marker[: self.msg_max_length]

        return sanitized

    def _format_syslog_message(
        self,
        severity: int,
        structured_data: str,
        message: str,
        event_type: str = None,
        timestamp: datetime = None,
    ) -> str:
        """Format complete syslog message.

        Args:
            severity: Syslog severity level (0-7)
            structured_data: RFC 5424 structured data (empty for RFC 3164)
            message: Log message content
            event_type: Event type for MSGID (RFC 5424 only)
            timestamp: Optional timestamp (computed if not provided)

        Returns:
            str: Complete syslog message
        """
        priority = self.facility * 8 + severity
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        if self.rfc_format == "5424":
            # RFC 5424 format - fix millisecond precision
            timestamp_str = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            # Use NIL value (-) when structured data is empty, use event_type as MSGID
            sd_part = structured_data if structured_data else "-"
            msgid = (
                event_type if event_type else "-"
            )  # Use event_type for MSGID when available
            header = f"<{priority}>1 {timestamp_str} {self._cached_hostname} {self.app_name} {self._cached_process_id} {msgid} {sd_part}"
            return f"{header} {message}"
        else:
            # RFC 3164 format (ensure day is space-padded, not zero-padded)
            timestamp_str = timestamp.strftime("%b %e %H:%M:%S").replace("  ", " ")
            header = f"<{priority}>{timestamp_str} {self._cached_hostname} {self.app_name}[{self._cached_process_id}]:"
            return f"{header} {message}"

    # The following are stubs for a future network transport implementation
    # async def _safe_log_with_network(self, message: str):
    #     """Safely log message with network transport if configured."""
    #     # Always write to file first (via base class)
    #     self._safe_log(message)

    #     # Then send via network if configured
    #     if self.transport in ["udp", "tcp", "tls"]:
    #         try:
    #             await self._send_via_network(message)
    #         except Exception as e:
    #             # Network failure handled in _send_via_network
    #             pass

    # async def log_request(self, request: MCPRequest, decision: PolicyDecision, server_name: str) -> None:
    #     """Log an incoming request and its security decision."""
    #     # Store timestamp for duration calculation
    #     self._store_request_timestamp(request)

    #     # Format and log the request
    #     log_message = self._format_request_log(request, decision, server_name)
    #     await self._safe_log_with_network(log_message)

    # async def log_response(self, request: MCPRequest, response: MCPResponse, decision: PolicyDecision, server_name: str) -> None:
    #     """Log a response to a request with the security decision."""
    #     # Calculate duration and add to metadata
    #     duration_ms = self._calculate_duration(request.id)
    #     enhanced_decision = self._enhance_decision_with_duration(decision, duration_ms)

    #     # Format and log the response
    #     log_message = self._format_response_log(request, response, enhanced_decision, server_name)
    #     await self._safe_log_with_network(log_message)

    # async def log_notification(self, notification: MCPNotification, decision: PolicyDecision, server_name: str) -> None:
    #     """Log a notification message."""
    #     # Format and log the notification
    #     log_message = self._format_notification_log(notification, decision, server_name)
    #     await self._safe_log_with_network(log_message)


# Policy manifest for policy-based plugin discovery
POLICIES = {"syslog_auditing": SyslogAuditingPlugin}
