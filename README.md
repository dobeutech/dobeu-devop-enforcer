# Dobeu Undertaker

**DevOps Standards Enforcement & Agent Orchestrator**

[![Azure Pipelines](https://dev.azure.com/dobeutech/dobeu-undertaker/_apis/build/status/main?branchName=main)](https://dev.azure.com/dobeutech/dobeu-undertaker/_build)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

Dobeu Undertaker is a Claude Agent SDK-powered DevOps automation platform that enforces coding standards, compliance policies, and orchestrates specialized AI agents across multi-repository environments with Azure platform integration.

## Features

- 🔍 **Multi-Agent Orchestration**: Coordinates 6 specialized agents for comprehensive code analysis
- 🔐 **Security Scanning**: Detects secrets, vulnerabilities, and OWASP Top 10 issues
- 📝 **Code Style Enforcement**: Validates formatting, naming conventions, and best practices
- ✅ **Compliance Checking**: Ensures license compliance, required files, and policy adherence
- 🧪 **Test Quality Analysis**: Verifies coverage, identifies anti-patterns
- 📚 **Documentation Validation**: Checks README, API docs, and changelog completeness
- 📦 **Dependency Auditing**: Scans for CVEs and outdated packages
- ☁️ **Azure Integration**: Native DevOps, Monitor, and Key Vault integration

## Quick Start

### Installation

```bash
# Install from PyPI
pip install dobeu-undertaker

# Or with Poetry
poetry add dobeu-undertaker
```

### Basic Usage

```bash
# Scan current directory
dobeu-undertaker scan

# Scan specific repository
dobeu-undertaker scan --repo /path/to/repo

# Generate compliance report
dobeu-undertaker report --output report.json --format json

# Enforce standards with auto-fix
dobeu-undertaker enforce --fix

# Watch mode for continuous monitoring
dobeu-undertaker watch --repos ./repo1,./repo2 --interval 300
```

### Programmatic Usage

```python
import asyncio
from dobeu_undertaker import DobeuOrchestrator, UndertakerConfig

async def main():
    config = UndertakerConfig()
    orchestrator = DobeuOrchestrator(config=config)

    # Run compliance scan
    results = await orchestrator.scan_repository(
        repo_path=Path("./my-repo"),
        parallel=True,
    )

    # Generate report
    await orchestrator.generate_report(
        repo_path=Path("./my-repo"),
        output_path=Path("./compliance-report.json"),
        report_format="json",
    )

asyncio.run(main())
```

## Configuration

### Repository Configuration

Create `.dobeu/config.yaml` in your repository:

```yaml
# Inherit base standards
inherit:
  - dobeu-base
  - dobeu-python  # For Python projects

# Override specific settings
overrides:
  standards:
    line_length: 120
    min_coverage_percent: 85

  # Disable specific rules
  disabled_rules:
    - STYLE003  # Allow TODO without ticket
```

### Global Configuration

Create `~/.dobeu/config.yaml` for organization-wide settings:

```yaml
environment: production

azure:
  organization: your-org
  project: your-project

notifications:
  enabled: true
  slack_webhook_url: https://hooks.slack.com/...
  notify_on_critical: true
  notify_on_high: true
```

## Specialized Agents

| Agent | Description |
|-------|-------------|
| **SecurityAgent** | Scans for secrets, OWASP vulnerabilities, injection risks |
| **CodeStyleAgent** | Validates formatting, naming, imports, type hints |
| **ComplianceAgent** | Checks licenses, required files, git workflow |
| **TestingAgent** | Analyzes coverage, test quality, anti-patterns |
| **DocumentationAgent** | Validates README, API docs, changelogs |
| **DependencyAuditAgent** | Scans for CVEs, outdated packages |

## Azure DevOps Integration

Add the pipeline template to your repository:

```yaml
# azure-pipelines.yml
resources:
  repositories:
    - repository: undertaker
      type: github
      name: dobeutech/dobeu-undertaker
      ref: main

extends:
  template: templates/azure-pipeline-template.yml@undertaker
  parameters:
    scanOnPR: true
    failOnCritical: true
```

## Docker

```bash
# Build
docker build -t dobeu-undertaker .

# Run scan
docker run -v $(pwd):/workspace \
  -e ANTHROPIC_API_KEY=xxx \
  dobeu-undertaker scan --repo /workspace
```

## Standards Library

Pre-defined standards configurations:

- `dobeu-base` - Foundation standards for all projects
- `dobeu-python` - Python-specific standards (ruff, pytest, typing)
- `dobeu-typescript` - TypeScript/JavaScript standards (eslint, prettier)
- `dobeu-infrastructure` - IaC standards (Terraform, Docker, K8s)

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key |
| `AZURE_DEVOPS_PAT` | Azure DevOps Personal Access Token |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Azure Monitor connection |
| `DOBEU_ENVIRONMENT` | Environment (development/staging/production) |

## Development

```bash
# Clone repository
git clone https://github.com/dobeutech/dobeu-undertaker.git
cd dobeu-undertaker

# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run linting
poetry run ruff check src/
poetry run pyright src/

# Build Docker image
docker build -t dobeu-undertaker:dev --target development .
```

## License

Proprietary - Copyright (c) 2025 Dobeu Tech Solutions LLC

## Support

- **Documentation**: [docs.dobeu.net](https://docs.dobeu.net)
- **Issues**: [GitHub Issues](https://github.com/dobeutech/dobeu-undertaker/issues)
- **Email**: support@dobeu.net
