# Centralize Plugin Options and Add Configuration Validation

## Overview

Replace hardcoded option strings scattered throughout security plugins with centralized constants and add proper validation for unknown configuration options. Currently, plugins silently ignore unsupported options (like "eye_color" for PII detection), creating confusion and potential configuration drift.

## Problem Statement

### Current Issues

1. **Hardcoded strings everywhere**: Each plugin has option names scattered throughout:
   - `describe_status()` methods: "Email", "Phone", "Credit Card" 
   - Pattern compilation: "email", "phone", "credit_card"
   - Format mappings: "us", "uk", "eu", "international"
   - Tests: Repeated option names in test configurations

2. **Silent failure on unknown options**: 
   - User configures `{"eye_color": {"enabled": true}}` in PII plugin
   - Plugin starts successfully but silently ignores the option
   - No patterns compiled, no detection happens, no warning given
   - Typos like "emial" instead of "email" go unnoticed

3. **Maintenance burden**:
   - Adding new options requires updates in multiple places
   - Risk of inconsistency between display names and internal keys
   - No single source of truth for supported options

### Affected Plugins

- **PII Filter** (`pii.py`): email, phone, credit_card, national_id, ssn + formats
- **Secrets Filter** (`secrets.py`): aws_access_keys, github_tokens, google_api_keys, etc.
- **Prompt Injection** (`prompt_injection.py`): Pattern categories and types

## Solution Design

### Phase 1: Centralize Constants

Create class-level constants at the top of each plugin file:

#### PII Filter Plugin
```python
class BasicPIIFilterPlugin(SecurityPlugin):
    # PII type identifiers and display names
    PII_TYPES = {
        'email': 'Email',
        'phone': 'Phone', 
        'credit_card': 'Credit Card',
        'national_id': 'SSN/ID',
        'ssn': 'SSN/ID'  # Alias for national_id
    }
    
    # Supported formats for each PII type
    PII_FORMATS = {
        'phone': ['us', 'uk', 'eu', 'international'],
        'national_id': ['us', 'uk_ni', 'canadian_sin'],
        'ssn': ['us'],
        'credit_card': ['all']
    }
    
    # Valid action types
    ACTIONS = ['block', 'redact', 'audit_only']
```

#### Secrets Filter Plugin
```python 
class SecretsFilterPlugin(SecurityPlugin):
    # Secret type identifiers and display names
    SECRET_TYPES = {
        'aws_access_keys': 'AWS Keys',
        'github_tokens': 'GitHub',
        'google_api_keys': 'Google API',
        'jwt_tokens': 'JWT',
        'slack_tokens': 'Slack',
        'private_keys': 'Private Keys',
        'generic_secrets': 'Generic',
        'aws_secret_keys': 'AWS Secret'
    }
    
    # Valid action types
    ACTIONS = ['block', 'redact', 'audit_only']
```

#### Prompt Injection Plugin
```python
class PromptInjectionDefensePlugin(SecurityPlugin):
    # Pattern category identifiers and display names
    PATTERN_CATEGORIES = {
        'common_injections': 'Common Injections',
        'bypass_attempts': 'Bypass Attempts', 
        'encoding_attacks': 'Encoding Attacks',
        'instruction_manipulation': 'Instruction Manipulation',
        'role_play': 'Role Play',
        'data_extraction': 'Data Extraction'
    }
    
    # Valid action types
    ACTIONS = ['block', 'audit_only']
```

### Phase 2: Add Configuration Validation

Add strict validation during plugin initialization:

```python
def _validate_configuration(self, config: Dict[str, Any]) -> None:
    """Validate configuration against supported options."""
    
    # Validate action
    action = config.get('action')
    if action not in self.ACTIONS:
        raise ValueError(f"Invalid action '{action}'. Must be one of: {', '.join(self.ACTIONS)}")
    
    # Validate PII types (for PII plugin)
    pii_types = config.get('pii_types', {})
    for pii_type in pii_types.keys():
        if pii_type not in self.PII_TYPES:
            raise ValueError(f"Unsupported PII type '{pii_type}'. Must be one of: {', '.join(self.PII_TYPES.keys())}")
    
    # Validate formats for each PII type
    for pii_type, pii_config in pii_types.items():
        if isinstance(pii_config, dict) and 'formats' in pii_config:
            formats = pii_config['formats']
            valid_formats = self.PII_FORMATS.get(pii_type, [])
            for format_name in formats:
                if format_name not in valid_formats and format_name != 'all':
                    raise ValueError(f"Unsupported format '{format_name}' for PII type '{pii_type}'. Must be one of: {', '.join(valid_formats)}")
```

### Phase 3: Replace Hardcoded Strings

Update all methods to use the centralized constants:

#### Status Description
```python
@classmethod
def describe_status(cls, config: Dict[str, Any]) -> str:
    # OLD: hardcoded strings
    # if pii_types.get("email", {}).get("enabled", False):
    #     enabled.append("Email")
    
    # NEW: use constants
    enabled = []
    pii_types = config.get("pii_types", {})
    for pii_type, display_name in cls.PII_TYPES.items():
        if pii_types.get(pii_type, {}).get("enabled", False):
            enabled.append(display_name)
```

#### Pattern Compilation
```python
def _compile_patterns(self):
    # OLD: hardcoded checks
    # if self.pii_types.get("email", {}).get("enabled"):
    
    # NEW: iterate over constants
    for pii_type in self.PII_TYPES.keys():
        if self.pii_types.get(pii_type, {}).get("enabled"):
            self._compile_pii_patterns(pii_type)
```

## Implementation Tasks

### Phase 1: PII Filter Plugin
- [ ] Define `PII_TYPES`, `PII_FORMATS`, and `ACTIONS` constants
- [ ] Add `_validate_configuration()` method
- [ ] Update `describe_status()` to use constants
- [ ] Update `_compile_patterns()` to iterate over constants
- [ ] Update `_expand_all_formats()` to use format constants
- [ ] Replace hardcoded strings in detection methods

### Phase 2: Secrets Filter Plugin  
- [ ] Define `SECRET_TYPES` and `ACTIONS` constants
- [ ] Add configuration validation
- [ ] Update `describe_status()` method
- [ ] Update pattern compilation logic
- [ ] Replace hardcoded strings throughout

### Phase 3: Prompt Injection Plugin
- [ ] Define `PATTERN_CATEGORIES` and `ACTIONS` constants
- [ ] Add configuration validation
- [ ] Update status description logic
- [ ] Replace hardcoded strings in pattern methods

### Phase 4: Update Tests
- [ ] Add tests for configuration validation (invalid options should fail)
- [ ] Add tests for typos in option names (should fail)
- [ ] Update existing tests to use constants where appropriate
- [ ] Add tests for edge cases in validation

### Phase 5: Documentation Updates
- [ ] Update plugin documentation to reference the centralized constants
- [ ] Update configuration examples to show supported options
- [ ] Document the validation behavior in user guides

## Benefits

1. **Single source of truth** - Each option defined once at the top of the file
2. **Early failure detection** - Invalid configurations fail at startup with clear messages  
3. **Better maintainability** - Add/remove options in one place
4. **IDE support** - Constants can be autocompleted and refactored
5. **Self-documenting** - Constants at the top serve as documentation
6. **Consistent naming** - Clear separation between display names and internal keys
7. **Typo prevention** - Misspelled options cause immediate failure

## Error Message Examples

```
# Before: Silent failure
User configures: {"pii_types": {"emial": {"enabled": true}}}
Result: Plugin starts, no email detection happens, no feedback

# After: Clear error
User configures: {"pii_types": {"emial": {"enabled": true}}} 
Result: ValueError: "Unsupported PII type 'emial'. Must be one of: email, phone, credit_card, national_id, ssn"
```

## Backward Compatibility

- **No breaking changes** - All existing valid configurations continue to work
- **Enhanced validation** - Only invalid configurations that were silently ignored before will now fail
- **Clear migration path** - Error messages will guide users to correct configuration

## Success Metrics

- [ ] No hardcoded option strings outside of the constant definitions
- [ ] All invalid configuration options cause startup failure with helpful messages
- [ ] All existing valid configurations continue to work
- [ ] Tests cover validation of all supported and unsupported options
- [ ] Documentation clearly shows supported options for each plugin