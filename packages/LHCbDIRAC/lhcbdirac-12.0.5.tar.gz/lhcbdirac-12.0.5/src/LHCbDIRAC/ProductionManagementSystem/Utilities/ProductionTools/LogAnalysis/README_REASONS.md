# LHCb Job Failure Reasons Configuration

This directory contains the configuration system for defining and managing job failure reason patterns used in LHCb production analysis.

## Overview

The failure reason system has been refactored to use a **YAML-based configuration** with **Pydantic validation**. This provides:

- **Easy configuration**: Define new failure reasons in YAML without writing Python code
- **Strong validation**: Pydantic ensures patterns are valid regex and configuration is correct
- **Flexibility**: Keep custom implementations in Python when needed
- **Maintainability**: Centralized configuration with validation and testing tools

## File Structure

```
LogAnalysis/
├── reasons.yaml              # YAML configuration for all failure reasons
├── reason_models.py          # Pydantic models with validation
├── reasons.py                # Main module (loads YAML + custom classes)
├── base_reasons.py           # Base reason classes
├── migrate_to_yaml.py        # Migration script (for reference)
└── test_reasons.py           # Comprehensive tests
```

## Quick Start

### Using Existing Reasons

```python
from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.LogAnalysis.reasons import (
    FunctorCompilationFailure,
    FatalGaudiError,
    EventWatchdog,
)

# All reason classes are available for import
print(FunctorCompilationFailure.pattern)
print(FatalGaudiError.explanation)
```

### Adding a New Reason

Add a new entry to `reasons.yaml`:

```yaml
- name: MyNewFailure
  base: KnownUnrecoverableFailure
  patterns:
    - "ERROR Something went wrong with [^\\n]+"
    - "FATAL Another pattern"
  explanation: "Description of what this failure means"
  issue_url: "https://gitlab.cern.ch/lhcb/project/-/issues/123"
```

Pydantic automatically validates patterns when loading. The new class will be automatically available:

```python
from .reasons import MyNewFailure
```

## YAML Configuration Format

### Basic Structure

```yaml
reasons:
  - name: ReasonClassName
    base: BaseReasonType
    patterns:
      - "regex pattern 1"
      - "regex pattern 2"
    explanation: "Human-readable explanation"
    issue_url: "https://gitlab.cern.ch/..."  # Optional
    custom_implementation: false  # Default: false
```

### Fields

- **name** (required): Python class name (must start with uppercase)
- **base** (required): Base class, one of:
  - `WorkerNodeIssue`
  - `RecoverableFailure`
  - `KnownUnrecoverableFailure`
  - `EventTimeout`
  - `RecoverableFailureWithManualIntervention`
  - `UnknownFailure`
- **patterns** (required): List of regex patterns (as strings)
- **explanation** (optional): Human-readable description
- **issue_url** (optional): Link to GitLab issue or documentation
- **mixin** (optional): Mixin class to customize behavior (e.g., `.reasons:FatalGaudiErrorMixin`)

### Pattern Format

Patterns are regular expressions as strings. Important notes:

1. **Escape backslashes**: In YAML, use `\\` for regex `\`
   - Good: `"ERROR\\s+Failed"`
   - Bad: `"ERROR\s+Failed"` (YAML interprets `\s`)

2. **Quotes for special characters**: Use quotes if pattern contains `:`, `[`, `{`, etc.
   - `"Error: .+"`
   - `'[ERROR] .+'`

3. **Multi-line patterns**: Literal newlines are preserved:
   ```yaml
   patterns:
     - "Line 1\\nLine 2"  # Matches actual newline
   ```

## Custom Behavior with Mixins

Some reason classes need custom logic (e.g., custom `match_string` property). Define mixin classes that inherit from `ReasonMixin` in `reasons.py`, then reference them in the YAML configuration:

**In reasons.py:**
```python
from .base_reasons import ReasonMixin

class FatalGaudiErrorMixin(ReasonMixin):
    """Mixin for FatalGaudiError to extract full error context."""

    @property
    def match_string(self) -> str:
        """Extract FATAL/ERROR lines leading up to the match."""
        log = self._job.files.steps[-1].application_log
        # ... custom implementation ...
        return log[start : self._end].decode(errors="backslashreplace")
```

**In reasons.yaml:**
```yaml
- name: FatalGaudiError
  base: UnknownFailure
  patterns:
    - '\sFATAL\s.*\n(?:.+\s(FATAL|ERROR)\s.*\n)*'
  mixin: .reasons:FatalGaudiErrorMixin
  explanation: A unrecognized fatal error occurred in Gaudi.
```

### Mixin Guidelines

1. **Inherit from ReasonMixin**: All mixin classes must inherit from `base_reasons.ReasonMixin`
2. **Override allowed methods**: Only override methods defined in `ReasonMixin` (currently: `match_string`)
3. **Use properties**: Methods that should be properties (like `match_string`) should use `@property`
4. **Module path format**: Use `.reasons:ClassName` for relative imports within the LogAnalysis package
5. **MRO placement**: Mixins are placed before the base class in the method resolution order

## Validation

Validation happens automatically via Pydantic when the YAML file is loaded. If there are any issues with the configuration, you'll get a clear error message.

### Manual Validation

To validate without importing the full module:

```python
from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.LogAnalysis.reason_models import ReasonsConfig

try:
    config = ReasonsConfig.load_from_yaml()
    print(f"✓ Configuration is valid! {len(config.reasons)} reasons defined.")
except Exception as e:
    print(f"✗ Validation failed: {e}")
```

Pydantic validates:
- All patterns compile as valid regex (as bytes)
- Pattern syntax and escaping
- Unique reason names
- Valid base class types
- Required fields are present

## Testing

Run the test suite:

```bash
pytest test_reasons.py -v
```

Tests cover:
- Pydantic model validation
- YAML loading
- Class creation
- Pattern compilation
- Module imports

## Environment Variables

- **DIRAC_PROD_MANAGER_REASONS_PATH**: Override the default `reasons.yaml` location

```bash
export DIRAC_PROD_MANAGER_REASONS_PATH=/path/to/custom/reasons.yaml
```

## Order of Reasons

**Important**: The order of reasons in `reasons.yaml` matters! Patterns are checked in order, and the first match wins. Place more specific patterns before more general ones.

```yaml
reasons:
  # More specific - checked first
  - name: SpecificError
    patterns: ["Very specific error pattern"]

  # More general - checked later
  - name: GenericError
    patterns: ["ERROR .+"]
```

## Best Practices

1. **Test patterns**: Use `check_patterns.py` before committing
2. **Add explanations**: Help others understand what the failure means
3. **Link to issues**: Include `issue_url` for known bugs
4. **Use specific patterns**: Avoid overly broad regex that might match unrelated errors
5. **Document changes**: Update this README if you add new base classes or features

## Examples

### Simple Failure Reason

```yaml
- name: DiskFull
  base: WorkerNodeIssue
  patterns:
    - "No space left on device"
    - "Disk quota exceeded"
  explanation: "The worker node ran out of disk space."
```

### Multiple Patterns

```yaml
- name: XRootDFailure
  base: RecoverableFailure
  patterns:
    - "\\[ERROR\\] Server responded with an error"
    - "\\[FATAL\\] Connection error"
    - "\\[FATAL\\] Hand shake failed"
  explanation: "An error occurred while trying to open a file using XRootD."
```

### With Issue URL

```yaml
- name: ReportedBug123
  base: KnownUnrecoverableFailure
  patterns:
    - "ERROR Specific bug pattern"
  explanation: "This is a known bug in version X.Y"
  issue_url: "https://gitlab.cern.ch/lhcb/project/-/issues/123"
```

## Troubleshooting

### Pattern Not Matching

1. Check regex syntax: `python -c "import re; re.compile(rb'your pattern')"`
2. Remember patterns are bytes: use `rb"pattern"` in Python tests
3. Check escaping: YAML strings need `\\` for literal backslash

### Validation Error

```bash
python check_patterns.py
```

This will show exactly which pattern is invalid and why.

### Import Error

Ensure the YAML file exists and is valid:

```python
from .reason_models import ReasonsConfig
config = ReasonsConfig.load_from_yaml()
# Will show detailed error if YAML is invalid
```

## Contributing

When adding new reason classes:

1. Add to `reasons.yaml`
2. Run `python check_patterns.py` to validate
3. Test the pattern against actual log samples
4. Add tests if needed in `test_reasons.py`
5. Update this README if adding new patterns or base classes

## Technical Details

### How It Works

1. **Startup**: `reasons.py` imports `ReasonsConfig` from `reason_models.py`
2. **Load YAML**: `ReasonsConfig.load_from_yaml()` reads `reasons.yaml`
3. **Validate**: Pydantic validates all fields, including regex patterns
4. **Create Classes**: `ReasonDefinition.to_class()` dynamically creates Python classes
5. **Register**: Classes are added to module globals via `globals().update()`
6. **Import**: Classes are available for import like any normal Python class

### Performance

- YAML loading and class creation happens once at import time
- No runtime overhead compared to pure Python definitions
- Hyperscan database compilation is unchanged

## Related Files

- [base_reasons.py](base_reasons.py) - Base reason class definitions
- [job_analyzer.py](job_analyzer.py) - Uses reason classes for log analysis
