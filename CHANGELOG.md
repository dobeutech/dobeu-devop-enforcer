# Changelog

All notable changes to Dobeu Undertaker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-12-15

### Added

- Initial release of Dobeu Undertaker
- **Core Orchestrator**: Main agent orchestration engine with parallel execution support
- **Security Agent**: Scans for secrets, OWASP vulnerabilities, and insecure patterns
- **Code Style Agent**: Validates formatting, naming conventions, and imports
- **Compliance Agent**: Checks licenses, required files, and git workflow
- **Testing Agent**: Analyzes test coverage and identifies anti-patterns
- **Documentation Agent**: Validates README, API docs, and changelogs
- **Dependency Audit Agent**: Scans for CVEs and outdated packages
- **Configuration System**: Pydantic-based config with YAML support and inheritance
- **Azure DevOps Integration**: Pipeline status updates and PR comments
- **Azure Monitor Integration**: OpenTelemetry-based telemetry export
- **Notification Service**: Slack, Teams, and email notifications
- **Standards Library**: Pre-defined standards for Python, TypeScript, and infrastructure
- **CLI Interface**: Typer-based CLI with scan, enforce, report, and watch commands
- **Docker Support**: Multi-stage Dockerfile for production deployment
- **Azure Pipeline Templates**: Reusable templates for repository integration

### Security

- Secrets detection patterns for common API keys and credentials
- OWASP Top 10 vulnerability checking
- Dependency vulnerability scanning

### Documentation

- Comprehensive README with quick start guide
- Standards YAML documentation
- Azure integration guide
- API reference (in code docstrings)

---

[Unreleased]: https://github.com/dobeutech/dobeu-undertaker/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/dobeutech/dobeu-undertaker/releases/tag/v0.1.0
