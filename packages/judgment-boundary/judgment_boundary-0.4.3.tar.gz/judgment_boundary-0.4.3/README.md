# Judgment Boundary

**A Responsibility Layer for Automated Systems**

> **"This is not a system that manages AI.
> This is infrastructure that makes judgment unavoidable."**

---

## What This Is

**Judgment Boundary** is a pre-action governance gate that sits between model output and organizational action. It enforces responsibility checkpoints before any automated system can act.

**Purpose**: Document and enforce the boundary between what an organization will and will not automate with AI.

---

## What This Is NOT

* ❌ An AI model or LLM platform
* ❌ A decision automation system
* ❌ A training or fine-tuning framework
* ❌ A machine learning system

---

## What This DOES

* ✅ Declares execution readiness (STOP / HOLD / ALLOW / INDET)
* ✅ Records organizational boundaries as immutable attestations
* ✅ Generates regulatory evidence (EU AI Act Article 14 compliance)
* ✅ Maintains external judgment state (no model modification)

---

## Where This Applies

**Regulatory Context:**
- EU AI Act Article 14 (Human Oversight Requirements)
- GDPR Article 22 (Automated Decision-Making)
- High-risk AI systems requiring accountability checkpoints

**Technical Context:**
- Pre-action governance gates
- Responsibility documentation
- Audit trail generation

---

## Documentation

* **System Specification**: [Whitepaper v1.0](./whitepaper/WHITEPAPER_v1.0.md)
* **EU AI Act Reference**: [Architecture Documentation](./architecture/eu_ai_act/)
* **Live Demonstrations**: [Regulatory Demos](./demos/)

---

## Installation

```bash
pip install judgment-boundary
```

Or via Docker:

```bash
docker pull judgment-boundary:latest
```

---

## Quick Start

```python
from judgment_boundary import JudgmentRuntime

runtime = JudgmentRuntime(
    memory_store_path="./judgment_memory.jsonl",
    enable_organizational_memory=True
)

result = runtime.process(
    prompt="What is the CEO salary?",
    model_output="The CEO salary is $500,000.",
    rag_sources=None,
    domain_tag="hr"
)

print(f"Decision: {result.decision}")  # STOP
print(f"Reason: {result.reason}")      # EVIDENCE_MISSING
```

---

## Core Architecture

```
[ Organizational Action ]
          ↑
[ Judgment Boundary Layer ]  ← Responsibility checkpoint
          ↑
[ Model Output ]
```

**Key Properties:**
- External state only (no model weights modified)
- Model-agnostic (works with any LLM/automation)
- Deterministic and reproducible
- Verifiable and auditable

---

## Demos

**Regulatory Compliance:**
- [EU AI Act HR Case](./demos/regulatory/eu_ai_act_hr_case.md)
- [Audit Walkthrough](./demos/regulatory/audit_walkthrough.md)

**Live Execution:**
- [HR Stop Demo](./demos/live/hr_stop_demo.sh)
- [Finance Hold Demo](./demos/live/finance_hold_demo.sh)

---

## License

MIT

---

## Status

This is a **public baseline** release documenting a working system.
For technical specification, see [Whitepaper v1.0](./whitepaper/WHITEPAPER_v1.0.md).
