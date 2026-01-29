# Judgment Boundary

Judgment Boundary is an organizational infrastructure that prevents irresponsible automation and proves that prevention.

---

## What This Is

Judgment Boundary is:

* **A judgment boundary layer** that enforces STOP / HOLD / ALLOW / INDETERMINATE decisions before automation
* **A governance and attestation system** that records organizational boundaries and declarations
* **A deterministic, external-state infrastructure** with no machine learning or model modification
* **A system that proves non-automation** through verifiable attestations and cryptographic hashes

---

## What This Is NOT

* ❌ **Not an AI model** - Does not generate, predict, or infer
* ❌ **Not an LLM wrapper** - Works independently of any model
* ❌ **Not a decision-making system** - Does not make automated decisions
* ❌ **Not a learning system** - Uses only frequency counting and repetition detection
* ❌ **Not an automation engine** - Prevents automation, does not enable it

---

## System Position

```
[ Application / Workflow ]
        ↓
[ AI / LLM / Heuristics ]
        ↓
[ Judgment Boundary ]   ← THIS SYSTEM
        ↓
[ Automation / Execution ]
```

Judgment Boundary does not decide. It prevents decisions that an organization is not willing to take responsibility for.

---

## Core Capabilities

### v0.1: Boundary Enforcement

Stop automation when:
- Evidence is missing
- Assertions are unverified
- Risk thresholds are exceeded

**Decision Types**: STOP | HOLD | ALLOW | INDETERMINATE

### v0.2: Organizational Character

Aggregate judgment patterns into organizational profiles using:
- Frequency counting (no ML)
- Repetition detection (no statistics)
- Temporal stability (deterministic)

### v0.3: Governance & Accountability

- **Boundary Declarations**: Change organizational character only through explicit declarations
- **Human Overrides**: Record human interventions separately (excluded from pattern learning)
- **Priority Hierarchy**: Override > Declaration > Profile > Individual Judgment

### v0.4: External Attestation

Generate immutable attestations with:
- Cryptographic hashes (SHA-256)
- Evidence packs (JSON + Markdown)
- External explanations (Auditor / Regulator / Contract views)

---

## 5-Minute Quickstart

### Installation

```bash
pip install -e .
```

### Basic Usage

```python
from judgment import JudgmentRuntime
from models.schemas import DomainTag

# Initialize runtime
runtime = JudgmentRuntime(
    memory_store_path="./judgment_memory.jsonl",
    enable_organizational_memory=True
)

# Execute judgment boundary check
result = runtime.process(
    prompt="What is the CEO salary?",
    model_output="The CEO definitely earns $500,000.",
    rag_sources=None,  # No evidence
    domain_tag=DomainTag.HR
)

print(f"Decision: {result.judgment_result.decision.value}")  # STOP
print(f"Reasons: {result.judgment_result.reason_slots}")      # EVIDENCE_MISSING
```

### Build Organizational Profile

```python
# After accumulating 20+ judgments
profile = runtime.build_organizational_profile()

# Explain organizational character
explanation = runtime.explain_organizational_character(DomainTag.HR)
print(explanation)
# "This organization is very conservative in the 'hr' domain..."
```

### Create Attestation

```python
from judgment.attestation import BoundaryAttestationBuilder

builder = BoundaryAttestationBuilder(runtime_version="v0.4.0")
attestation = builder.build_attestation(
    organization_id="my-org",
    org_profile=profile,
    active_declarations=declarations
)

print(f"Attestation ID: {attestation.attestation_id}")
print(f"Profile Hash: {attestation.profile_hash}")
print(f"Immutable: {attestation.immutable}")  # True
```

---

## Architecture

### Boundary Decision Module

Evaluates boundary conditions:
- Evidence availability
- Assertion verification
- Risk patterns
- Domain constraints

**No model calls. No API requests. Deterministic logic only.**

### Organizational Memory

Aggregates judgment history into boundary profiles:
- Frequency: How often each decision occurred
- Repetition: Consecutive decision patterns
- Stability: Consistency over time

**No machine learning. No statistical models. Simple counters only.**

### Governance Layer

Enforces organizational boundaries:
- **Declarations**: Explicit boundary statements (e.g., "AUTOMATION_NOT_ALLOWED")
- **Overrides**: Human interventions (always excluded from pattern learning)
- **Priority**: Override > Declaration > Profile > Individual

**Changes require human accountability. No automatic updates.**

### Attestation Layer

Generates verifiable proof:
- Immutable attestation with cryptographic hashes
- Evidence pack documenting how profiles were built
- External explanations for auditors, regulators, contracts

**Hash-verifiable. Reproducible. Tamper-evident.**

---

## Use Cases

### Compliance & Audit

Generate attestations for:
- Regulatory submissions (EU AI Act, GDPR Art.22)
- Audit documentation
- Compliance verification

### Contract Incorporation

Include attestation references in:
- Service agreements
- Vendor contracts
- Liability frameworks

### Organizational Governance

Establish and enforce:
- Domain-specific boundaries (HR, Finance, Legal)
- Automation restrictions
- Human oversight requirements

---

## Key Principles

### 1. External State

All judgment patterns stored externally, not in models:
- Append-only JSONL traces
- JSON organizational profiles
- JSONL declaration events

**State persists across restarts. Model-agnostic.**

### 2. Deterministic Operation

No randomness. No optimization. No learning loops:
- Same input → Same hash
- Reproducible attestations
- Verifiable by recomputation

**Predictable. Auditable. Explainable.**

### 3. Human Accountability

All boundary changes require human authorization:
- Declarations must specify issuer and justification
- Overrides always exclude from pattern learning
- Complete audit trail maintained

**No automatic evolution. No silent changes.**

### 4. Separation of Concerns

Clear boundaries between layers:
- Judgment ≠ Automation
- Override ≠ Learning
- Declaration ≠ Profile update

**Each layer has single responsibility.**

---

## Documentation

### Implementation Guides

- [MASTER_WORK_ORDER.md](./MASTER_WORK_ORDER.md) - Complete system specification
- [LOCAL_IMPLEMENTATION_v01.md](./LOCAL_IMPLEMENTATION_v01.md) - v0.1: Boundary Runtime
- [LOCAL_IMPLEMENTATION_v02.md](./LOCAL_IMPLEMENTATION_v02.md) - v0.2: Organizational Memory
- [LOCAL_IMPLEMENTATION_v03.md](./LOCAL_IMPLEMENTATION_v03.md) - v0.3: Governance & Override
- [LOCAL_IMPLEMENTATION_v04.md](./LOCAL_IMPLEMENTATION_v04.md) - v0.4: External Attestation

### Architecture

- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture and design principles

### Distribution

- [DISTRIBUTION_D1_CLI.md](./DISTRIBUTION_D1_CLI.md) - CLI packaging guide
- [DISTRIBUTION_D2_SDK.md](./DISTRIBUTION_D2_SDK.md) - SDK stabilization guide

---

## Version History

### v0.4.0 (Current)

- **External Attestation Layer**: Immutable attestations with cryptographic hashes
- Evidence pack generation (JSON + Markdown)
- External explanations (Auditor / Regulator / Contract)
- Attestation registry

### v0.3.0

- **Governance & Override Layer**: Boundary declarations and human overrides
- Profile explainer (Paragraph / Bullet / Formal formats)
- Governance priority engine
- Override pattern learning exclusion

### v0.2.0

- **Organizational Memory Layer**: Judgment aggregation into profiles
- Boundary strength classification
- Temporal stability analysis
- Profile persistence and reload

### v0.1.0

- **Boundary Runtime**: STOP / HOLD / ALLOW / INDETERMINATE decisions
- Judgment trace storage
- Negative proof generation
- Online adaptation engine

---

## Installation

### Requirements

- Python 3.8+
- Pydantic 2.0+

### Install from Source

```bash
git clone https://github.com/YOUR_ORG/judgment-boundary.git
cd judgment-boundary
pip install -e .
```

---

## Examples

See `examples/` directory:

- `v01_completion_demo.py` - Boundary enforcement demonstration
- `v02_organizational_memory_demo.py` - Profile aggregation demonstration
- `v03_governance_demo.py` - Governance and override demonstration
- `v04_attestation_demo.py` - Attestation generation demonstration

---

## Testing

```bash
# Run tests
python tests/test_decision.py
python tests/test_memory.py
python tests/test_runtime.py

# Run demos
python examples/v01_completion_demo.py
python examples/v02_organizational_memory_demo.py
python examples/v03_governance_demo.py
python examples/v04_attestation_demo.py
```

---

## Contributing

Judgment Boundary v0.4.0 is architecturally complete.

**Accepted contributions**:
- Bug fixes
- Documentation improvements
- Test coverage expansion
- Distribution tooling (CLI, packaging)

**Not accepted**:
- New judgment logic
- Learning algorithms
- Model integration features
- Optimization loops

---

## Versioning Policy

Judgment Boundary follows **Semantic Versioning 2.0.0** with strict governance constraints.

### Version Format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Semantic or responsibility changes (architecturally prohibited in v0.4.x)
- **MINOR**: New distribution channels only (PyPI, Docker, etc.)
- **PATCH**: Bug fixes with no behavior change

### Current Version: `0.4.0`

All v0.4.x releases are semantically identical. Your code will continue to work without changes.

**Contract Guarantee**: Type semantics, API signatures, and decision meanings will not change within v0.4.x series.

For detailed versioning policy, see [SDK.md](./SDK.md).

---

## License

MIT License

---

## Contact & Support

For questions about:
- **Compliance**: Review attestation documentation in `attestation_explanations/`
- **Integration**: See implementation guides in `LOCAL_IMPLEMENTATION_*.md`
- **Auditing**: Generate attestation with `v04_attestation_demo.py`

---

## Final Statement

**This system does not automate decisions.**

**It proves which decisions were never automated.**

---

**Status**: v0.4.0 - Architecturally Complete
**Architecture**: Deterministic | External State | Model-Agnostic | Accountable
