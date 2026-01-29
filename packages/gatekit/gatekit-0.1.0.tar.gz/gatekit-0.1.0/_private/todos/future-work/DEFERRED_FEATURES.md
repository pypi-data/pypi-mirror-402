# Deferred Features for JSON Lines Auditing Plugin

## Features Deferred to Future Release

The following features have been implemented but deferred from the v0.1.0 release due to bugs in the compliance metadata generation:

### 1. Compliance Schema Support
- **Config Option**: `compliance_schema` (standard/grc_standard/financial_services)
- **Purpose**: Adds regulatory compliance metadata to audit logs
- **Bug**: Uses mock objects instead of actual MCP messages, breaking `isinstance()` checks
- **Impact**: `evidence_type` always returns "UNKNOWN_EVIDENCE", `governance_category` can't detect tool calls

### 2. Risk Metadata
- **Config Option**: `include_risk_metadata`
- **Purpose**: Adds risk assessment and compliance metadata to logs
- **Depends on**: Compliance schema implementation

### 3. API Compatibility Metadata
- **Config Option**: `api_compatible`
- **Purpose**: Adds API version and schema version fields
- **Depends on**: Compliance metadata framework

### Implementation Details

The full implementation with these features is preserved in:
- `/future-work/json_lines_with_compliance.py`

The implementation includes:
- 9 compliance-specific methods for metadata generation
- SOX control objectives mapping
- GRC category classification
- Risk level assessment
- Evidence type classification
- Audit trail ID generation

### Fix Required

To enable these features in a future release:
1. Fix the mock object issue - pass actual MCP message objects or store message type in extracted data
2. Test the `isinstance()` checks work correctly
3. Verify compliance metadata values are accurate
4. Add integration tests for each compliance schema type

### Features Kept in v0.1.0

The following features ARE working and included:
- `redact_request_fields` - Successfully redacts sensitive fields from request bodies
- `include_request_body` - Controls whether request parameters are logged
- Basic JSON/JSONL formatting with `pretty_print` option
- All core auditing functionality