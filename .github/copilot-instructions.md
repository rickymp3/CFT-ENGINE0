# CFT-ENGINE0 Copilot Instructions

## Project Overview
CFT-ENGINE0 is a minimal Python engine project serving as a foundation for future configuration-driven execution capabilities. Currently implements a basic status-reporting engine with expansion planned for configuration parsing, multi-environment execution, and artifact generation.

## Dev Container Setup

### Canonical Development Environment
This project uses GitHub Codespaces/VS Code dev containers as the **primary development environment**. The dev container (`mcr.microsoft.com/devcontainers/universal:2`) provides:
- **Python 3.12.1** with pip 25.1.1
- Pre-configured workspace at `/workspaces/CFT-ENGINE0`
- All tests, builds, and experiments should run inside this container

### First-Time Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python engine.py
python -m pytest
```

### Critical: Pytest Collection Issue
**Never create `test_engine.py` in the project root.** Pytest will fail with import file mismatch errors if test files exist in both root and `tests/` directories. Always place tests in `tests/test_engine.py`.

If you encounter `import file mismatch` errors:
```bash
rm -f test_engine.py
rm -rf __pycache__
python -m pytest
```

## Architecture

### Current Structure
```
/workspaces/CFT-ENGINE0/
├── engine.py              # Main engine entry point (keep minimal)
├── tests/                 # Canonical test location (pytest auto-discovery)
│   └── test_engine.py
├── requirements.txt       # Python dependencies (currently: pytest)
├── architecture_test_plan.md  # Future feature roadmap
└── .devcontainer/         # Dev container configuration
```

### Core Components
- **`engine.py`**: Single-file engine implementation with `run()` (returns status string) and `main()` (CLI entry point). Keep this minimal—complex logic should be factored into separate modules as the project grows.
- **`tests/test_engine.py`**: Canonical test location for pytest discovery. **Do not duplicate tests in project root.**

### Planned Architecture (per `architecture_test_plan.md`)
The project will expand to include:

**Configuration System** (not yet implemented):
- Format: YAML/JSON (TBD), location: `/config/engines/*.yaml` (TBD)
- Top-level config objects planned:
  - `project`: Project metadata and settings
  - `engine`: Orchestration logic and request routing
  - `runtime`: Execution environment configuration
  - `profile`: Environment-specific overrides (dev/prod)
  - `pipeline_step`: Individual processing stages
  
**Example Future Config** (illustrative):
```yaml
# config/engines/default.yaml (planned, not implemented)
engine:
  model: "gpt-4"                    # Underlying model/backend
  orchestration: "sequential"       # How requests are routed
  vars:                             # Parameter sets
    temperature: 0.7
    max_tokens: 2048
  soft_limits:                      # Resource caps
    tokens_per_minute: 10000
    max_concurrent: 5
```

**Multi-environment support**: Configuration overrides via `config.dev.yaml`, `config.prod.yaml`
**Artifact generation**: Logs, reports, and generated assets
**Error recovery**: Diagnostic logging and failsafe paths

## Development Workflows

### Running the Engine
```bash
python engine.py
```
Expected output: `CFT-ENGINE0 engine is running.`

### Testing
```bash
python -m pytest          # Run all tests
python -m pytest -v       # Verbose output
python -m pytest tests/test_engine.py::test_run_returns_status_message  # Single test
```

**Test Expectations**:
- Tests use pytest's `capsys` fixture for capturing stdout
- All tests currently expect the exact string: `"CFT-ENGINE0 engine is running."`
- When adding tests, follow the pattern in `tests/test_engine.py`

### Dependencies
Managed via `requirements.txt`:
- `pytest` is the only current dependency
- Use `pip install -r requirements.txt` for setup
- No package.json, setup.py, or pyproject.toml—this is intentionally minimal

### Tooling Available in Dev Container
- **Python**: 3.12.1 (at `/home/codespace/.python/current/bin/python`)
- **Package Manager**: pip 25.1.1
- **Test Runner**: pytest (installed via requirements.txt)
- **No formatters/linters configured yet** (Black, Pylint, etc. not in requirements.txt)
- Standard Linux CLI tools: git, curl, wget, grep, find, etc.

## Environment & Secrets

### Current State
- **No environment variables required** for basic operation
- **No secrets management** implemented yet
- Engine runs without external dependencies or configuration files

### Planned Pattern (not implemented)
When configuration support is added:
- Local development: `.env` files (not committed to git)
- CI/CD: GitHub Secrets for sensitive values
- Dev container: Environment variables via `devcontainer.json` `remoteEnv` section
- **Never hardcode** API keys, tokens, or credentials in config files

## Ports & Services

### Current State
- **No services or ports** exposed—this is a CLI-only tool
- No API server, database, message broker, or web UI

### Future Considerations
If the engine expands to include services:
- Reserve port 8000 for API server (standard Python convention)
- Document any containerized vs. host-local service assumptions
- Update `devcontainer.json` with `forwardPorts` configuration

## Code Conventions

### Testing Patterns
- **Assertion style**: Use exact string equality (`assert run() == "CFT-ENGINE0 engine is running."`)
- **Output testing**: Use `capsys.readouterr()` for validating printed output, strip trailing newlines
- **Test structure**: Separate tests for function return values vs. side effects (stdout)

### Function Design
- Functions should return values (`run()`) separately from side effects (`main()`)
- Entry point pattern: `if __name__ == "__main__": main()`
- Include type hints (`-> str`, `-> None`)
- Module docstrings use triple-quoted strings at the top

### Future Testing Strategy (from test plan)
When implementing new features, follow this pattern:
1. **Unit tests**: Focus on configuration parsing, field validation, type coercion
2. **Integration tests**: End-to-end runs with fixtures for sample projects and expected outputs
3. **Error-path validation**: Test malformed configs, missing dependencies, timeout scenarios
4. **Fixtures**: Use dedicated fixture files (minimal configs, legacy formats, golden outputs)

## Key Files
- `engine.py`: Main engine implementation
- `tests/test_engine.py`: Canonical test location (pytest auto-discovery)
- `architecture_test_plan.md`: Roadmap for test expansion and future features
- `requirements.txt`: Python dependencies
- `.devcontainer/devcontainer.json`: Dev container configuration

## Development Notes
- The project is intentionally minimal as a starting point
- Root-level `test_engine.py` duplicates `tests/test_engine.py`—prefer adding tests to `tests/` directory
- When adding configuration support, reference the test plan for validation and error-handling requirements
- Keep the core engine simple; complex functionality should be modularized into separate files

## Future Implementation Checklist

When implementing planned features, analyze these components:

**Entry Points & Bootstrapping**:
- `engine.py`: Currently minimal; will expand to include config loading orchestration
- Future: Separate `cli.py` or `main.py` if command-line complexity grows

**Configuration Loading & Validation**:
- Not yet implemented—will likely use Pydantic models or JSON Schema
- Config files will live in `/config/engines/*.yaml` (planned)
- Validation should happen before execution, with clear error messages

**Engine Orchestration Layer**:
- Not yet implemented—will route requests, manage pipelines, compose backends
- Key decision: Sequential vs. parallel execution model
- Integration with external LLM APIs or local models (TBD)

**Tests & Fixtures**:
- `tests/test_engine.py`: Currently basic unit tests
- Future: Add `tests/integration/` for end-to-end scenarios
- Fixtures: Minimal configs, malformed configs, golden outputs (see `architecture_test_plan.md`)

**CI/CD & Scripts**:
- No `.github/workflows/` or `/scripts/` directory yet
- When added, document build/test/deploy assumptions
- Likely: pytest in CI, version tagging, release automation
