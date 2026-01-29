# jps-nextflow-utils

![Build](https://github.com/jai-python3/jps-nextflow-utils/actions/workflows/test.yml/badge.svg)
![Publish to PyPI](https://github.com/jai-python3/jps-nextflow-utils/actions/workflows/publish-to-pypi.yml/badge.svg)
[![codecov](https://codecov.io/gh/jai-python3/jps-nextflow-utils/branch/main/graph/badge.svg)](https://codecov.io/gh/jai-python3/jps-nextflow-utils)

**Offline analysis of Nextflow run artifacts** - audit, report, and compare workflow runs without network calls or runtime dependencies.

## 🚀 Overview

`jps-nextflow-utils` provides a **Typer-based CLI** for read-only analysis of Nextflow workflow run artifacts. It helps pipeline developers, platform engineers, and QA teams understand what happened during workflow execution by analyzing logs, traces, configs, and other static outputs.

### Key Features

- 🔍 **Artifact Discovery** - Automatically finds and fingerprints Nextflow run artifacts
- 📊 **Metadata Extraction** - Extracts run details, versions, executors, timings from logs
- ⚠️ **Failure Detection** - Classifies errors (OOM, timeouts, containers, filesystem, etc.)
- 📈 **Performance Analysis** - Computes process-level statistics from trace files
- 🔄 **Run Comparison** - Diff two runs to identify behavioral/performance changes
- 📋 **Batch Processing** - Audit multiple runs and generate aggregate summaries
- 🎯 **Rules Engine** - Extensible YAML-based pattern matching for custom checks
- 📝 **Multiple Output Formats** - JSON, Markdown, text, CSV, NDJSON

### Out of Scope

- Triggering or modifying workflow runs
- Network calls (Tower API, cloud APIs)
- Domain-specific scientific validation

## 📦 Installation

### From Source

```bash
git clone https://github.com/jai-python3/jps-nextflow-utils.git
cd jps-nextflow-utils
pip install -e .
```

### Using Make

```bash
make install
```

## 🎯 Quick Start

### Audit a Single Run

```bash
# Basic audit with text output
nf-audit audit run --run-dir /path/to/nextflow/run

# Generate JSON report
nf-audit audit run --run-dir ./my_run --format json --outdir ./reports

# Generate Markdown report
nf-audit audit run -d ./my_run -f md -o ./reports
```

### Batch Audit Multiple Runs

```bash
# Discover and audit all runs in a directory
nf-audit audit batch --base-dir ./all_runs --glob "*" --outdir ./batch_reports

# Audit specific directories
nf-audit audit batch --run-dir ./run1 --run-dir ./run2 --outdir ./reports
```

### Compare Two Runs

```bash
# Diff two runs
nf-audit diff --run-a ./run_baseline --run-b ./run_test

# Save diff report
nf-audit diff -a ./run_baseline -b ./run_test --outdir ./diffs
```

### Work with Rules

```bash
# List built-in rules
nf-audit rules list

# List rules from custom pack
nf-audit rules list --rules ./examples/custom_rules.yaml

# Test rules against a run
nf-audit rules test --target ./my_run --rules ./examples/nfcore_rules.yaml
```

## 📖 Usage Examples

### Example 1: Audit with Custom Rules

```bash
nf-audit audit run \
  --run-dir /data/pipeline_runs/2024-01-15_rnaseq \
  --format json \
  --outdir /reports \
  --rules ./examples/custom_rules.yaml \
  --rules ./examples/nfcore_rules.yaml
```

### Example 2: Batch Processing with CSV Summary

```bash
nf-audit audit batch \
  --base-dir /data/all_runs \
  --glob "run_*" \
  --outdir /batch_output \
  --summary-format csv
```

### Example 3: Performance Comparison

```bash
# Compare before and after optimization
nf-audit diff \
  --run-a /runs/before_optimization \
  --run-b /runs/after_optimization \
  --outdir /comparison
```

## 📁 Expected Artifacts

The tool discovers and analyzes these common Nextflow artifacts:

- `.nextflow.log` - Main Nextflow log
- `nextflow.config` - Configuration files
- `trace.txt` - Process execution trace
- `report.html` - HTML report
- `timeline.html` - Timeline visualization
- `dag.html` / `dag.dot` - Workflow DAG
- `params.json` / `params.yaml` - Parameters
- Additional `*.config` and `*.log` files

## 🔧 Output Formats

### JSON Report Schema

```json
{
  "schema_version": "1.0.0",
  "tool_version": "0.1.0",
  "generated_at": "2024-01-17T10:30:00",
  "run_dir": "/path/to/run",
  "overall_status": "ERROR",
  "metadata": {
    "run_name": "angry_euler",
    "nextflow_version": "23.04.1",
    "executor": "slurm",
    "duration_seconds": 3600.5
  },
  "findings": [...],
  "process_rollups": [...],
  "inventory": {...}
}
```

### Markdown Report

Human-readable report with:
- Run metadata summary
- Findings by severity
- Process statistics table
- Artifact inventory
- Evidence excerpts

### Batch CSV Summary

Aggregate metrics across runs:
- Run status and duration
- Finding counts by severity
- Top failing processes
- Task success/failure rates

## 🎨 Custom Rules

Create custom YAML rule packs:

```yaml
version: "1.0"

rules:
  - id: custom_error_pattern
    category: process_failure
    severity: ERROR
    description: "Custom error detection"
    scope: log
    confidence: 0.9
    patterns:
      - "CUSTOM_ERROR_\\d+"
      - "MyPipeline failed"
    remediation: |
      Check pipeline logs for specific error details.
      Contact support if issue persists.
```

See [examples/](examples/) for more rule pack examples.

## 🧪 Development

### Setup

```bash
# Clone and install with dev dependencies
git clone https://github.com/jai-python3/jps-nextflow-utils.git
cd jps-nextflow-utils
pip install -e ".[dev]"
```

### Testing

```bash
# Run tests
make test

# Run with coverage
pytest --cov=src/jps_nextflow_utils tests/

# Lint and format
make fix
make format
make lint
```

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Security scan
bandit -r src/
```

## 📊 Exit Codes

The CLI uses exit codes to indicate run status:

- `0` - OK (no findings above INFO)
- `1` - WARN (warnings present)
- `2` - FAIL (errors or fatal findings)
- `≥3` - Tool/runtime error

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

See [docs/Development_SOP.md](docs/Development_SOP.md) for details.

## 📝 Documentation

- [Development SOP](docs/Development_SOP.md)
- [Release SOP](docs/Release_SOP.md)
- [Example Rules](examples/)

## 🐛 Reporting Issues

Found a bug or have a feature request? Please open an issue on GitHub:
https://github.com/jai-python3/jps-nextflow-utils/issues

## 📜 License

MIT License © Jaideep Sundaram

## 🙏 Acknowledgments

Designed for the Nextflow and nf-core communities.

---

**Built with** 🐍 Python | 🎨 Typer | 📊 Nextflow
