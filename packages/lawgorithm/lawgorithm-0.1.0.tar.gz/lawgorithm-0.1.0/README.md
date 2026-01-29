# Lawgorithm Python SDK

Official Python SDK for [Lawgorithm](https://lawgorithm.io) - AI Act Compliance Platform.

[![PyPI version](https://badge.fury.io/py/lawgorithm.svg)](https://badge.fury.io/py/lawgorithm)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install lawgorithm
```

## Quick Start

```python
from lawgorithm import LawgorithmClient

# Initialize the client
client = LawgorithmClient(
    api_url="https://api.lawgorithm.io",
    api_token="your-api-token"
)

# List your AI systems
systems = client.list_systems()
for system in systems:
    print(f"{system.name}: {system.risk_level}")

# Run compliance check
result = client.check_compliance(
    repo="myorg/myrepo",
    commit="abc123",
    branch="main"
)

print(f"Compliance rate: {result.compliance_rate * 100:.1f}%")
if result.issues:
    for issue in result.issues:
        print(f"  [{issue.severity}] {issue.message}")
```

## Features

### AI System Management

```python
# Create a new AI system
system = client.create_system(
    name="Credit Scoring Model",
    description="ML model for credit risk assessment",
    purpose="Automated credit decisions",
    domain="finance"
)

# Classify risk level using AI
system = client.classify_system(system.id)
print(f"Risk level: {system.risk_level}")  # e.g., "high"
print(f"Justification: {system.risk_justification}")
```

### Compliance Checks (CI/CD)

```python
# Standard check (returns result)
result = client.check_compliance(
    repo="myorg/myrepo",
    commit="abc123",
    strict=False
)

# Strict mode (raises exception on failure)
try:
    result = client.check_compliance(
        repo="myorg/myrepo",
        commit="abc123",
        strict=True
    )
except ComplianceError as e:
    print(f"Blocked: {e.message}")
    for issue in e.issues:
        print(f"  - {issue['message']}")
    sys.exit(1)
```

### Post-Market Surveillance (AI Act Article 72)

```python
# Create an incident
incident = client.create_incident(
    system_id=system.id,
    title="Bias detected in predictions",
    severity="high",
    category="bias_detected",
    description="Model shows 15% higher rejection rate for protected group"
)

# Notify competent authority
incident = client.notify_authority(incident.id)

# Get incident statistics
stats = client.get_incident_stats(system.id)
print(f"Total incidents: {stats.total}")
print(f"Authority notifications: {stats.authority_notifications}")
```

### Compliance Dossier ("Le Dossier Vivant")

```python
# Check dossier completeness
completeness = client.check_dossier_completeness(system.id)
print(f"Complete: {completeness.overall_complete}")
print(f"Progress: {completeness.completion_percentage:.1f}%")
print(f"Missing: {completeness.missing_obligations}")

# Export full dossier
dossier = client.export_dossier(system.id, format="markdown")
with open("compliance_dossier.md", "w") as f:
    f.write(dossier.content)
```

### Attestations (Ed25519)

```python
# Create a signed attestation
attestation = client.create_attestation(
    system_id=system.id,
    attestation_type="CONFORMITY_DECLARATION",
    statement="This system complies with AI Act requirements",
    private_key=my_private_key,  # Ed25519 private key (base64)
    attester_org="Acme Corp",
    attester_role="DPO"
)

# Verify attestation
result = client.verify_attestation(attestation.id)
print(f"Valid: {result['valid']}")
```

### MLOps Integration

```python
# Import MLflow run as evidence
result = client.import_mlflow_run(
    system_id=system.id,
    tracking_uri="http://mlflow.internal:5000",
    run_id="abc123def456"
)
print(f"Evidence created: {result['evidence_id']}")

# Import Weights & Biases run
result = client.import_wandb_run(
    system_id=system.id,
    entity="myteam",
    project="credit-model",
    run_id="xyz789",
    api_key="your-wandb-key"
)
```

### Compliance State History

```python
# Get compliance history
history = client.get_compliance_history(system.id, limit=10)
for state in history:
    print(f"{state.created_at}: {state.compliance_score:.1%} ({state.trigger})")

# Verify chain integrity (tamper detection)
result = client.verify_compliance_chain(system.id)
if result["valid"]:
    print("Chain integrity verified")
else:
    print(f"Chain broken at: {result['broken_at']}")
```

## Context Manager

The client can be used as a context manager for automatic cleanup:

```python
with LawgorithmClient(api_url="...", api_token="...") as client:
    systems = client.list_systems()
    # Connection is automatically closed
```

## Error Handling

```python
from lawgorithm import (
    LawgorithmClient,
    LawgorithmError,
    AuthenticationError,
    ComplianceError,
    NotFoundError,
    ValidationError,
)

try:
    result = client.check_compliance(strict=True)
except AuthenticationError:
    print("Invalid API token")
except NotFoundError:
    print("System not found")
except ComplianceError as e:
    print(f"Compliance failed: {len(e.issues)} issues")
except ValidationError as e:
    print(f"Invalid request: {e.errors}")
except LawgorithmError as e:
    print(f"API error [{e.status_code}]: {e.message}")
```

## Environment Variables

You can configure the client via environment variables:

```bash
export LAWGORITHM_API_URL="https://api.lawgorithm.io"
export LAWGORITHM_API_TOKEN="your-api-token"
```

```python
import os
from lawgorithm import LawgorithmClient

client = LawgorithmClient(
    api_url=os.environ.get("LAWGORITHM_API_URL", "http://localhost:8000/api"),
    api_token=os.environ.get("LAWGORITHM_API_TOKEN")
)
```

## Requirements

- Python 3.10+
- httpx
- pydantic

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [Documentation](https://docs.lawgorithm.io)
- [API Reference](https://api.lawgorithm.io/docs)
- [Lawgorithm Platform](https://lawgorithm.io)
