# Phase 8: Implement PipelineResult Collection System

## Overview
Currently, the PluginManager accumulates all plugin results into a single final PluginResult, losing visibility into what each individual plugin did. This phase implements the ProcessingPipeline and PipelineStage classes that already exist but are unused, providing complete visibility into the plugin processing chain.

## Problem Statement
1. **Lost Visibility**: When multiple plugins process a request, we only see the final accumulated result, not what each plugin did
2. **Poor Debugging**: Can't trace which plugin made which modification or decision
3. **No Performance Metrics**: Can't identify which plugins are slow
4. **Unused Classes**: ProcessingPipeline and PipelineStage classes exist in `gatekit/plugins/interfaces.py` but are never used
5. **Audit Trail**: Auditing plugins can't see the complete processing history
6. **Security vs Error Ambiguity**: Exceptions are indistinguishable from intentional security blocks
7. **Sensitive Data Exposure**: Full content capture risks leaking secrets through logs

## Requirements

### 1. Core Implementation

#### 1.0 Define Clear Outcome Enums
Define enums to prevent ambiguity and string-based errors:
```python
from enum import Enum

class StageOutcome(Enum):
    """Clear outcome for each pipeline stage"""
    PASSED = "passed"           # Plugin allowed request to continue
    BLOCKED = "blocked"         # Security plugin intentionally blocked
    MODIFIED = "modified"       # Plugin modified content
    COMPLETED = "completed"     # Plugin completed the request
    ERROR = "error"            # Plugin encountered an error

class PipelineOutcome(Enum):
    """Overall pipeline outcome"""
    ALLOWED = "allowed"                        # Request allowed through
    BLOCKED = "blocked"                        # Security blocked request
    NO_SECURITY_EVALUATION = "no_security"     # No security plugins evaluated
    ERROR = "error"                           # Pipeline error occurred
    COMPLETED = "completed"                    # Middleware completed request
```

#### 1.1 Update PluginManager Methods
The following methods in `gatekit/plugins/manager.py` must be updated to return ProcessingPipeline instead of PluginResult:
- `process_request(request, server_name) -> ProcessingPipeline`
- `process_response(request, response, server_name) -> ProcessingPipeline`
- `process_notification(notification, server_name) -> ProcessingPipeline`

#### 1.2 Create PipelineStages During Processing
For each plugin that runs, create a PipelineStage that captures:
```python
stage = PipelineStage(
    plugin_name=getattr(plugin, 'plugin_id', plugin.__class__.__name__),
    plugin_type="security" if isinstance(plugin, SecurityPlugin) else "middleware",
    input_content=current_content,  # The content going INTO this plugin (may be cleared later)
    output_content=modified_content,  # The content coming OUT (if modified)
    content_hash=hashlib.sha256(str(current_content).encode()).hexdigest(),  # Always captured
    result=plugin_result,  # The PluginResult returned by the plugin
    processing_time_ms=elapsed_time_in_ms,
    outcome=StageOutcome.PASSED,  # Set based on result
    error_type=None,  # Exception class name if error
    security_evaluated=isinstance(plugin, SecurityPlugin)  # Track if security plugin ran
)
pipeline.add_stage(stage)
```

#### 1.3 Track Content Transformations
- Start with the original request/response/notification
- Track each modification through the pipeline
- Set final_content to the last modified version (or original if unmodified)

#### 1.4 Content Capture Policy for v0.1.0
**Security-First Approach**: If any SecurityPlugin blocks or modifies content, don't capture full content in pipeline stages:
```python
def should_capture_content(self) -> bool:
    """Don't capture content if any security plugin blocked or modified"""
    for stage in self.stages:
        if stage.plugin_type == "security":
            if stage.result.allowed is False:  # Blocked
                return False
            if stage.result.modified_content is not None:  # Redacted/modified
                return False
    return True
```
This prevents sensitive data from being exposed in logs while maintaining full visibility for clean requests.

### 2. ProcessingPipeline Construction

#### 2.1 Initial Pipeline Setup
At the start of each process method:
```python
import time
import hashlib

pipeline = ProcessingPipeline(
    original_content=request,  # or response/notification
    stages=[],
    final_content=None,
    total_time_ms=0.0,
    pipeline_outcome=PipelineOutcome.NO_SECURITY_EVALUATION,  # Updated based on processing
    blocked_at_stage=None,
    completed_by=None,
    had_security_plugin=False,  # Track if any security plugin evaluated
    capture_content=True  # Will be set to False if security action occurs
)
start_time = time.monotonic()  # Use monotonic for accurate timing
```

#### 2.2 Processing Each Plugin
For each plugin:
```python
# Track the content going into this plugin
input_content = current_request  # or current_response/notification
stage_start = time.monotonic()  # Use monotonic for accurate timing

# Execute the plugin
outcome = StageOutcome.PASSED  # Default
error_type = None

try:
    result = await plugin.process_request(current_request, server_name)
    
    # Enforce SecurityPlugin contract (KEEP THIS!)
    if isinstance(plugin, SecurityPlugin):
        pipeline.had_security_plugin = True
        pipeline.pipeline_outcome = PipelineOutcome.ALLOWED  # Update from NO_SECURITY_EVALUATION
        if result.allowed is None:
            raise ValueError(f"Security plugin {plugin_name} failed to make a security decision")
        elif result.allowed is False:
            outcome = StageOutcome.BLOCKED
            pipeline.pipeline_outcome = PipelineOutcome.BLOCKED
    
    # Determine outcome based on result
    if result.modified_content:
        outcome = StageOutcome.MODIFIED
    elif result.completed_response:
        outcome = StageOutcome.COMPLETED
        pipeline.pipeline_outcome = PipelineOutcome.COMPLETED
    
except Exception as e:
    # Track error separately from security decision
    outcome = StageOutcome.ERROR
    error_type = type(e).__name__
    pipeline.pipeline_outcome = PipelineOutcome.ERROR
    result = PluginResult(allowed=False, reason=str(e))

stage_end = time.monotonic()
elapsed_ms = (stage_end - stage_start) * 1000

# Determine output content
output_content = None
if result.modified_content:
    output_content = result.modified_content
    current_request = result.modified_content  # Update for next plugin
elif result.completed_response:
    output_content = result.completed_response

# Check if we should stop capturing content
if isinstance(plugin, SecurityPlugin):
    if result.allowed is False or result.modified_content is not None:
        pipeline.capture_content = False

# Calculate content hash (always captured for lineage tracking)
content_hash = hashlib.sha256(str(input_content).encode()).hexdigest()

# Create and add the stage
stage = PipelineStage(
    plugin_name=getattr(plugin, 'plugin_id', plugin.__class__.__name__),
    plugin_type="security" if isinstance(plugin, SecurityPlugin) else "middleware",
    input_content=input_content,  # Temporarily store, will be cleared if needed
    output_content=output_content,  # Temporarily store, will be cleared if needed
    content_hash=content_hash,  # Always keep hash for lineage
    result=result,
    processing_time_ms=elapsed_ms,
    outcome=outcome,
    error_type=error_type,
    security_evaluated=isinstance(plugin, SecurityPlugin)
)
pipeline.add_stage(stage)

# Handle blocking/completion
if result.allowed is False:
    # Stop processing, return pipeline immediately
    pipeline.final_decision = False
    pipeline.blocked_at_stage = stage.plugin_name
    break
    
if result.completed_response:
    # Stop processing, return pipeline with completed response
    pipeline.completed_by = stage.plugin_name
    pipeline.final_content = result.completed_response
    break
```

#### 2.3 Finalizing the Pipeline
After all plugins (or early exit):
```python
end_time = time.monotonic()
pipeline.total_time_ms = (end_time - start_time) * 1000

# Set final content if not already set
if pipeline.final_content is None:
    pipeline.final_content = current_request  # or response/notification

# Retroactively clear content and reasons if security action occurred
# Auditing plugins can override this via their capture_sensitive_content config
if not pipeline.capture_content:
    for stage in pipeline.stages:
        # Clear content
        stage.input_content = None
        stage.output_content = None
        # Keep content_hash for lineage tracking
        
        # Clear reasons (they might contain sensitive data too)
        if stage.result.reason:
            # Replace with generic outcome-based reason
            stage.result.reason = f"[{stage.outcome.value}]"

return pipeline
```

#### 2.4 Configuration for Content Capture
Content capture behavior is controlled both globally and per auditing plugin:
```yaml
# In gatekit.yaml
plugins:
  global:
    capture_sensitive_content: false  # Global default for production safety
  auditing:
    _global:
      - policy: json_lines
        config:
          output_file: audit.jsonl
          capture_sensitive_content: true  # Override global for this plugin
          # When false: content and reasons cleared after security actions
          # When true: all content preserved even after blocks/modifications
```

```python
# Auditing plugins check both global and plugin-specific config
class JSONLinesAuditingPlugin(AuditingPlugin):
    def __init__(self, config: dict, global_config: dict = None):
        global_default = (global_config or {}).get('capture_sensitive_content', False)
        self.capture_sensitive_content = config.get('capture_sensitive_content', global_default)
    
    async def log_request(self, request: MCPRequest, pipeline: ProcessingPipeline, server_name: Optional[str] = None):
        # Use safe or full pipeline based on plugin config
        log_data = pipeline.to_audit_log(capture_sensitive=self.capture_sensitive_content)

### 3. Update ProxyServer Integration

#### 3.1 Update handle_request Method
In `gatekit/proxy/server.py`, update to work with ProcessingPipeline:

```python
# Old code:
decision = await self._plugin_manager.process_request(request, server_name)
if decision.allowed is False:
    # Block request

# New code:
pipeline = await self._plugin_manager.process_request(request, server_name)
if pipeline.pipeline_outcome == PipelineOutcome.BLOCKED:
    # Block request
    # Reason may be cleared if capture_sensitive_content=false
    logger.info(f"Request blocked by {pipeline.blocked_at_stage}: {pipeline.stages[-1].result.reason}")
elif pipeline.pipeline_outcome == PipelineOutcome.ERROR:
    # Handle error
    logger.error(f"Pipeline error at {pipeline.blocked_at_stage}: {pipeline.stages[-1].error_type}")
    
if pipeline.completed_by:
    # Request was completed by middleware
    response = pipeline.final_content
    logger.info(f"Request completed by {pipeline.completed_by}")
    return response

# Use the final transformed request
upstream_request = pipeline.final_content if isinstance(pipeline.final_content, MCPRequest) else request
```

#### 3.2 Update process_response Handling
Similar updates for response processing:
```python
response_pipeline = await self._plugin_manager.process_response(request, response, server_name)
if response_pipeline.pipeline_outcome in (PipelineOutcome.BLOCKED, PipelineOutcome.ERROR):
    # Response blocked or errored
    
# Use final transformed response
final_response = response_pipeline.final_content if isinstance(response_pipeline.final_content, MCPResponse) else response
```

### 4. Content Visibility Strategy

#### 4.1 Metadata Always Available
Regardless of security actions, the following metadata is ALWAYS captured:
- Plugin name and type
- Processing time
- Decision made (allowed/blocked/modified/completed)
- Reason for decision
- Error information if applicable
- Whether security plugins evaluated the request

#### 4.2 Content Capture Rules
Content (input_content/output_content) is captured based on security actions:
- **Clean requests**: Full content captured for observability
- **Security blocks**: Content NOT captured (sensitive)
- **Security modifications**: Content NOT captured (contains PII/secrets)
- **Errors**: Content NOT captured (may contain sensitive data in error state)

#### 4.3 Pipeline Methods for Safe Access
```python
class ProcessingPipeline:
    def to_audit_log(self, capture_sensitive: bool = False) -> Dict:
        """Return representation for audit logging based on sensitivity preference"""
        if capture_sensitive or self.capture_content:
            # Return full pipeline including any sensitive content
            return self.to_dict()
        
        # Return cleared version (default safe behavior)
        return {
            "stages": [stage.to_metadata_dict() for stage in self.stages],
            "pipeline_outcome": self.pipeline_outcome.value,
            "had_security_plugin": self.had_security_plugin,
            "blocked_at_stage": self.blocked_at_stage,
            "completed_by": self.completed_by,
            "total_time_ms": self.total_time_ms,
            "content_captured": False
        }
    
    def get_uncleaned_copy(self) -> 'ProcessingPipeline':
        """Get a copy with original content/reasons before clearing (for dev mode)"""
        # Returns deep copy with original data restored
        # Only available if called before finalization
```

### 5. Update Auditing Integration

#### 5.1 Pass Pipeline to Audit Plugins
Auditing plugins should receive the ProcessingPipeline so they can see the full processing history:

```python
# In log_request and log_response methods
await self._plugin_manager.log_request(request, pipeline, server_name)
await self._plugin_manager.log_response(request, response, response_pipeline, server_name)
```

#### 5.2 Update AuditingPlugin Interface
Update the log methods to accept ProcessingPipeline:
```python
async def log_request(
    self, 
    request: MCPRequest, 
    pipeline: ProcessingPipeline,  # Changed from PluginResult
    server_name: Optional[str] = None
) -> None:
    # Use plugin's own config to decide what to capture
    capture_sensitive = self.config.get('capture_sensitive_content', False)
    log_data = pipeline.to_audit_log(capture_sensitive=capture_sensitive)
    
    # Log appropriately based on plugin's needs
    await self._write_log(log_data)
    
async def log_response(
    self,
    request: MCPRequest,
    response: MCPResponse, 
    pipeline: ProcessingPipeline,  # Changed from PluginResult
    server_name: Optional[str] = None
) -> None:
    # Same approach - each auditing plugin decides based on its config
    capture_sensitive = self.config.get('capture_sensitive_content', False)
    log_data = pipeline.to_audit_log(capture_sensitive=capture_sensitive)
```

### 6. Testing Requirements

#### 6.1 Update Existing Tests
**NOTE**: Most individual plugin tests remain unchanged since plugins still return PluginResult.
Only tests of PluginManager and ProxyServer need updates:

```python
# Individual plugin tests - NO CHANGE:
result = await plugin.process_request(request, server_name)
assert result.allowed is True

# PluginManager tests - CHANGE:
# Old:
result = await manager.process_request(request, None)
assert result.allowed is True

# New:
pipeline = await manager.process_request(request, None)
assert pipeline.pipeline_outcome == PipelineOutcome.ALLOWED
assert pipeline.blocked_at_stage is None
```

#### 6.2 New Pipeline-Specific Tests
Create `tests/unit/test_processing_pipeline.py` with tests for:

1. **Pipeline Construction**:
   - Verify stages are created for each plugin
   - Check timing measurements
   - Verify content tracking

2. **Modification Tracking**:
   - Test that modifications are properly tracked
   - Verify input/output content for each stage
   - Check final_content is set correctly

3. **Blocking Behavior**:
   - Test that blocking stops the pipeline
   - Verify blocked_at_stage is set
   - Check that subsequent plugins don't run

4. **Completion Behavior**:
   - Test that completed_response stops the pipeline
   - Verify completed_by is set
   - Check final_content is the completed response

5. **Performance Metrics**:
   - Verify processing_time_ms is recorded
   - Check total_time_ms is sum of stages

6. **Content Capture Policy**:
   - Test that content is captured for clean requests
   - Verify content is NOT captured when security plugin blocks
   - Verify content is NOT captured when security plugin modifies
   - Check metadata is always available

7. **Error Classification**:
   - Test that errors set outcome=StageOutcome.ERROR
   - Verify error_type captures exception class
   - Check errors are distinguishable from security blocks

8. **Security Tracking**:
   - Verify had_security_plugin flag is set correctly
   - Test security_evaluated per stage
   - Check pipeline knows if security was involved

### 7. Implementation Order

1. **First**: Update interfaces.py with enums and enhanced dataclasses
2. **Second**: Update PluginManager to build and return ProcessingPipeline
3. **Third**: Update ProxyServer to use ProcessingPipeline
4. **Fourth**: Update auditing plugins to receive ProcessingPipeline (immediate)
5. **Fifth**: Update integration tests (PluginManager/ProxyServer only)
6. **Sixth**: Create new pipeline-specific tests

### 8. Critical Invariants to Maintain

1. **SecurityPlugin Contract**: SecurityPlugins MUST still set allowed to True/False, never None
2. **Early Exit**: If a plugin blocks or completes, no subsequent plugins should run
3. **Content Flow**: Each plugin receives the output of the previous plugin
4. **Error Handling**: Plugin errors should create a stage with outcome=StageOutcome.ERROR and synthetic PluginResult(allowed=False)
5. **No Behavior Changes**: The actual security decisions and content modifications should work exactly as before
6. **Content Safety**: Never capture content after security actions (blocks/modifications)
7. **Error Classification**: Errors must be distinguishable from intentional security blocks

### 9. Example Final Structure

After processing 3 plugins (middleware, security, middleware):
```python
# Note: Since PIIFilter modified content (security action), all content and reasons 
# are retroactively cleared. Auditing plugins with capture_sensitive_content=true
# can still access the original data via pipeline.to_audit_log(capture_sensitive=True)
pipeline = ProcessingPipeline(
    original_content=MCPRequest(...),
    stages=[
        PipelineStage(
            plugin_name="LoggingMiddleware",
            plugin_type="middleware",
            input_content=MCPRequest(...),
            output_content=None,  # No modification
            content_hash="a3f5e8...",  # Always captured
            result=PluginResult(allowed=None, reason="[passed]"),  # Originally "Logged", cleared retroactively
            processing_time_ms=0.5,
            outcome=StageOutcome.PASSED,
            error_type=None,
            security_evaluated=False
        ),
        PipelineStage(
            plugin_name="ToolAllowlist",
            plugin_type="security",
            input_content=MCPRequest(...),
            output_content=None,
            content_hash="a3f5e8...",
            result=PluginResult(allowed=True, reason="[passed]"),  # Originally "Tool allowed", cleared
            processing_time_ms=1.2,
            outcome=StageOutcome.PASSED,
            error_type=None,
            security_evaluated=True
        ),
        PipelineStage(
            plugin_name="PIIFilter",
            plugin_type="middleware",  
            input_content=None,  # Content cleared retroactively
            output_content=None,  # Content cleared retroactively
            content_hash="b4d8c1...",  # Hash still available for lineage
            result=PluginResult(allowed=None, modified_content=..., reason="[modified]"),  # Cleared
            processing_time_ms=2.3,
            outcome=StageOutcome.MODIFIED,
            error_type=None,
            security_evaluated=False
        )
    ],
    final_content=MCPRequest(...),  # The modified version from PIIFilter
    total_time_ms=4.0,
    pipeline_outcome=PipelineOutcome.ALLOWED,  # Security passed, request continues
    blocked_at_stage=None,
    completed_by=None,
    had_security_plugin=True,
    capture_content=False  # Set to False, content retroactively cleared
)
```

### 10. Success Criteria

1. All existing tests pass with minimal modifications
2. ProcessingPipeline provides complete visibility into plugin processing
3. Performance metrics are accurately tracked
4. The system behaves identically to before (just with better visibility)
5. Auditing plugins can access the full processing history (with content safety)
6. No performance regression (pipeline tracking should add minimal overhead)
7. Sensitive content is never exposed in logs after security actions
8. Errors are clearly distinguishable from security blocks
9. Security plugin involvement is trackable

## Notes for Implementation

- **DO NOT** change the security semantics - SecurityPlugins must still return allowed=True/False
- **DO NOT** skip the contract enforcement for SecurityPlugin
- **DO NOT** capture content after security blocks or modifications (v0.1.0 safety)
- **DO** preserve all existing error handling
- **DO** maintain early exit behavior for blocked/completed requests
- **DO** track timing using time.monotonic() for performance analysis
- **DO** test thoroughly - this touches core request flow
- **DO** distinguish errors from security decisions with StageOutcome.ERROR enum
- **DO** track security plugin involvement with had_security_plugin flag
- **DO** use PluginManager to handle all content clearing logic (not Pipeline)
- **DO** update existing PipelineStage and ProcessingPipeline dataclasses directly

## Files to Modify

1. `gatekit/plugins/interfaces.py` - Add enums and enhance dataclasses
2. `gatekit/plugins/manager.py` - Main implementation
3. `gatekit/proxy/server.py` - Update to use ProcessingPipeline
4. `gatekit/plugins/auditing/*.py` - Update audit plugins to receive ProcessingPipeline
5. `tests/unit/test_plugin_manager*.py` - Update PluginManager integration tests only
6. `tests/unit/test_proxy_server.py` - Update ProxyServer tests
7. `tests/unit/test_processing_pipeline.py` - New comprehensive test file