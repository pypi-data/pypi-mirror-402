# jps-controlled-vocabularies-utils

![Build](https://github.com/jai-python3/jps-controlled-vocabularies-utils/actions/workflows/test.yml/badge.svg)
![Publish to PyPI](https://github.com/jai-python3/jps-controlled-vocabularies-utils/actions/workflows/publish-to-pypi.yml/badge.svg)
[![codecov](https://codecov.io/gh/jai-python3/jps-controlled-vocabularies-utils/branch/main/graph/badge.svg)](https://codecov.io/gh/jai-python3/jps-controlled-vocabularies-utils)

A standalone Python package for loading, managing, and validating controlled vocabularies stored in YAML files.

## 🚀 Overview

`jps-controlled-vocabularies-utils` provides a complete solution for managing controlled vocabularies in Python applications. It enables you to:

- Define vocabularies in human-readable YAML files
- Load and query vocabularies with a simple API
- Validate values against term rules (allowed values, regex patterns)
- Search terms by name, key, or synonyms
- Get explainable validation results

Perfect for healthcare workflows, data pipelines, ETL validation, and any application requiring consistent terminology.

### Features

- **YAML-backed vocabulary registry** - Store vocabularies in version-controlled YAML files
- **Flexible parser** - Load from files, directories, or in-memory strings
- **Comprehensive validation** - Validate both registry integrity and runtime values
- **Pydantic models** - Full type safety with Pydantic v2
- **Smart key derivation** - Auto-generate stable keys from term names
- **Search capabilities** - Prefix, contains, and exact matching with case sensitivity options
- **Explainable results** - Detailed reasons for validation failures

### Example Usage

```python
from jps_controlled_vocabularies_utils import Parser, Validator

# Load vocabulary from YAML file
parser = Parser()
registry = parser.load_path("vocabularies/workflow_terms.yml")

# Query terms
vocab = registry.get_vocabulary("workflow.system_terminology")
term = registry.get_term("workflow.system_terminology", "readiness_status.ready")
print(f"{term.name}: {term.description}")

# Search terms
results = registry.search_terms("workflow.system_terminology", "ready")
print(f"Found {len(results)} matching terms")

# Validate values
validator = Validator()
result = validator.validate_value(
    registry,
    vocabulary_id="workflow.system_terminology",
    term_key="readiness_status.ready",
    value="Ready"
)

if result.is_valid:
    print("✓ Valid")
else:
    print(f"✗ Invalid: {', '.join(result.reasons)}")
```

## 📦 Installation

```bash
pip install jps-controlled-vocabularies-utils
```

### Development Installation

```bash
git clone https://github.com/jai-python3/jps-controlled-vocabularies-utils.git
cd jps-controlled-vocabularies-utils
pip install -e ".[dev]"
```

## 🧪 Development

### Setup

```bash
make install
```

### Testing and Quality

```bash
# Run tests
make test

# Format and lint
make fix && make format && make lint

# Type checking
mypy src
```

## 📖 Documentation

See [docs/](docs/) for detailed documentation including:

- YAML schema reference
- API documentation
- Configuration options
- Advanced usage examples

### Quick YAML Example

```yaml
schema_version: "1.0"
vocabulary_id: "workflow.system_terminology"
title: "Workflow Terminology"
description: "Core workflow terms"
terms:
  - key: readiness_status.ready
    name: "Ready"
    description: "All requirements satisfied"
    allowed_values: ["Ready", "ready"]
    tags: ["status"]
```

## 🛠️ Requirements

- Python 3.10+
- pydantic >= 2.0.0
- pyyaml >= 6.0.0

## 📜 License

MIT License © Jaideep Sundaram

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.

## 🔗 Links

- **Repository**: https://github.com/jai-python3/jps-controlled-vocabularies-utils
- **Issues**: https://github.com/jai-python3/jps-controlled-vocabularies-utils/issues
