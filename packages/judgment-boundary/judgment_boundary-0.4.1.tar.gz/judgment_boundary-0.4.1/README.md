# Echo Judgment System

**An Organizational Judgment Infrastructure for Accountable AI**

> **"우리는 AI를 관리하는 시스템을 만든 게 아니라,
> 조직이 판단을 회피하지 못하게 만드는 인프라를 만들고 있다."**

---

## 🎯 What This Is

**Echo Judgment System** is an **Organizational Judgment Infrastructure (OJI)** that remembers, explains, declares, and proves how an organization chooses *NOT* to automate decisions with AI.

**→ For complete implementation guidance from first principles, see [MASTER_WORK_ORDER.md](./MASTER_WORK_ORDER.md)**

**→ For v0.1 local implementation step-by-step guide, see [LOCAL_IMPLEMENTATION_v01.md](./LOCAL_IMPLEMENTATION_v01.md)**

**→ For v0.2 local implementation step-by-step guide, see [LOCAL_IMPLEMENTATION_v02.md](./LOCAL_IMPLEMENTATION_v02.md)**

**→ For v0.3 local implementation step-by-step guide, see [LOCAL_IMPLEMENTATION_v03.md](./LOCAL_IMPLEMENTATION_v03.md)**

**→ For v0.4 local implementation step-by-step guide, see [LOCAL_IMPLEMENTATION_v04.md](./LOCAL_IMPLEMENTATION_v04.md)**

**→ For CLI distribution guide (D1), see [DISTRIBUTION_D1_CLI.md](./DISTRIBUTION_D1_CLI.md)**

**→ For SDK distribution guide (D2), see [DISTRIBUTION_D2_SDK.md](./DISTRIBUTION_D2_SDK.md)**

### This System Does NOT

* ❌ Automate decisions
* ❌ Fine-tune AI models
* ❌ Train on user data
* ❌ Use machine learning or statistics

### This System DOES

* ✅ Record where the organization chose to stop automation
* ✅ Aggregate judgment patterns into organizational character
* ✅ Enforce boundaries through declarations (not training)
* ✅ Generate verifiable attestations for audits, regulators, and contracts

---

## 📛 Naming Framework

This system has multiple names depending on context:

* **Conceptual Name**: **Organizational Judgment Infrastructure (OJI)**
  → Judgment infrastructure at organizational level

* **Technical Name**: **Model-Agnostic Judgment Runtime**
  → External state, no model modification

* **External/Regulatory Name**: **AI Decision Boundary & Attestation System**
  → For EU AI Act, GDPR Art.22, compliance contexts

* **Project Name**: **Echo Judgment System**
  → Memory echoes, repeats, becomes character, returns as accountability

---

## 🔒 Core Principle

> **이 시스템은 AI를 학습시키지 않는다.**
> **AI를 사용하는 '판단 체계'를 학습시킨다.**
> **그 학습은 항상 외부에 남는다.**

**Learning happens in the Runtime, not in the model.**

---

## 🏗️ Architecture Evolution

### ✅ v0.1: External Accumulation Loop
**"Judgments can have memory."**

- Judgments stored externally (not in model)
- Patterns accumulated over time
- Future behavior modified by past patterns
- Model-agnostic (works with any LLM)

### ✅ v0.2: Organizational Memory Layer
**"Memory becomes organizational character."**

- Individual judgments → Organizational profile
- Character persists across sessions
- New instances inherit organizational memory
- Aggregation via frequency/repetition/temporal stability (no ML/stats)

### ✅ v0.3: Boundary Governance & Override
**"Organizational character is declared, explained, and accountable."**

- Profile explained in human language
- Changes via DECLARATION only (not automatic learning)
- Human overrides excluded from pattern learning
- Full accountability & traceability

### ✅ v0.4: External Attestation Layer
**"Proof of what the organization chose NOT to automate."**

- Immutable attestation with cryptographic hashes
- Evidence pack (JSON + Markdown)
- External explanations (Auditor/Regulator/Contract views)
- Attestation registry for historical tracking

---

## 📦 Installation

```bash
pip install -e .
```

---

## 🚀 Quick Start

### Basic Usage (v0.1)

```python
from judgment import JudgmentRuntime
from models.schemas import DomainTag

# Initialize Runtime
runtime = JudgmentRuntime(
    memory_store_path="./judgment_memory.jsonl",
    enable_adaptation=True,
    enable_negative_proof=True
)

# Process a judgment
result = runtime.process(
    prompt="What is the CEO salary?",
    model_output="The CEO salary is definitely $500,000.",
    rag_sources=None,  # No evidence
    domain_tag=DomainTag.HR,
    assumption_mode=False
)

print(f"Decision: {result.judgment_result.decision.value}")  # STOP
print(f"Action: {result.action.value}")
print(f"Content: {result.content}")
```

### Organizational Memory (v0.2)

```python
from judgment import JudgmentRuntime
from models.schemas import DomainTag

# Enable organizational memory
runtime = JudgmentRuntime(
    enable_organizational_memory=True,
    profile_store_path="./organization_profile.json",
    organization_id="my-org"
)

# 1. Accumulate judgments
for request in requests:
    runtime.process(...)

# 2. Build organizational profile
org_profile = runtime.build_organizational_profile()

# 3. Explain organizational character
print(runtime.explain_organizational_character(DomainTag.HR))
# → "이 조직은 'hr' 도메인에서 매우 보수적이며..."

# 4. Character persists across restarts
new_runtime = JudgmentRuntime(
    enable_organizational_memory=True,
    profile_store_path="./organization_profile.json"
)
# Profile automatically loaded, new requests inherit character
```

### Attestation Generation (v0.4)

```python
from judgment.attestation import BoundaryAttestationBuilder, AttestationExplainer

# Build attestation
builder = BoundaryAttestationBuilder(runtime_version="v0.4")
attestation = builder.build_attestation(
    organization_id="default",
    org_profile=org_profile,
    active_declarations=declarations
)

print(f"Attestation ID: {attestation.attestation_id}")
print(f"Profile Hash: {attestation.profile_hash}")
print(f"Immutable: {attestation.immutable}")

# Generate external explanations
explainer = AttestationExplainer()
auditor_view = explainer.explain_for_auditor(attestation, org_profile, declarations)
regulator_view = explainer.explain_for_regulator(attestation, org_profile, declarations)
contract_view = explainer.explain_for_contract(attestation, org_profile, declarations)
```

---

## 🧩 System Architecture

**→ For detailed architectural coordinates and design principles, see [ARCHITECTURE.md](./ARCHITECTURE.md)**

### Execution Flow

```
[User Input]
   ↓
[LLM (any provider)]
   ↓
[Judgment Runtime]
   ├─ Boundary Decision (STOP / HOLD / ALLOW / INDET)
   ├─ Reason Slots (EvidenceMissing, Conflict, OutOfScope, Risk…)
   ├─ Counterfactuals (negative proof)
   ↓
[Priority Hierarchy]
   ├─ Human Override (highest)
   ├─ Boundary Declaration
   ├─ Organizational Profile
   └─ Individual Judgment
   ↓
[Execution Router]
   ├─ Answer
   ├─ Ask Clarification
   ├─ Stop + Human Escalation
   ↓
[External State Storage]
   ├─ Judgment Memory (JSONL)
   ├─ Organizational Profile (JSON)
   ├─ Declarations (JSONL)
   ├─ Overrides (JSONL)
   └─ Attestations (JSONL)
```

### Layer Positioning (Architecture Coordinates)

**Where does Judgment Boundary Layer sit?**

```
[ External World ]
  (Regulator / Auditor / Contract)
          ↑
[ Attestation Layer ]        ← v0.4 (Immutable Responsibility)
          ↑
[ Governance Layer ]         ← v0.3 (Declarations / Overrides)
          ↑
[ Organizational Memory ]    ← v0.2 (Boundary Profile)
          ↑
[ Judgment Boundary Layer ]  ← 🔴 Runtime Gate
          ↑
[ LLM / Tool / RAG ]
          ↑
[ Raw Input ]
```

**Judgment Boundary Layer is:**

* **Above** the model
* **Below** the organization
* **At the entrance** of execution

**What it does:**

* Declares STOP / HOLD / ALLOW / INDET (does NOT make decisions)
* Attaches Reason Slots
* Generates Negative Proof
* Creates trace signatures
* Asks: **"Is this request in a state where judgment can begin?"**

**What it does NOT do:**

* ❌ Generate answers
* ❌ Search knowledge
* ❌ Optimize outputs

**Why it's outside the model:**

* Judgment subject is NOT the model
* Organizational character always takes priority
* Persists across restarts and model changes
* Can be frozen as attestation

**Layer relationships:**

* **Attestation**: Proof (v0.4)
* **Governance**: Declaration (v0.3)
* **Boundary**: Execution (v0.1-v0.2)
* **Model**: Generation

> **"Judgment Boundary Layer는
> 모델이 말하기 전에,
> 조직이 책임질 수 있는지 먼저 묻는 실행 게이트다."**

> **"이 레이어가 존재하는 순간,
> AI는 더 이상 '판단 주체'가 될 수 없다."**

---

## 🔍 Core Components

### v0.1: External Accumulation Loop

1. **Judgment Decision Module**: STOP/HOLD/ALLOW/INDET logic with reason slots
2. **Negative Proof Generator**: Documents rejected alternatives
3. **Judgment Memory Store**: Append-only storage (not logs, but learning state)
4. **Online Adaptation Engine**: Modifies future behavior based on patterns

### v0.2: Organizational Memory Layer

5. **Judgment Memory Aggregator**: Frequency + Repetition + Temporal Stability (no ML)
6. **Judgment Boundary Profile**: Organizational signature independent of individuals/sessions/models
7. **Organization Profile Store**: Human-readable JSON storage

### v0.3: Boundary Governance & Override

8. **Boundary Profile Explainer**: Human language generation (Paragraph/Bullet/Formal)
9. **Boundary Declaration Store**: Changes via explicit declarations only
10. **Human Override Store**: Separate channel with `exclude_from_pattern_learning=True`
11. **Boundary Diff Engine**: Organization A vs B comparison

### v0.4: External Attestation Layer

12. **Boundary Attestation Builder**: Immutable attestations with SHA-256 hashes
13. **Attestation Evidence Pack**: JSON + Markdown evidence bundles
14. **Attestation Explainer**: Auditor/Regulator/Contract views
15. **Attestation Registry**: Historical tracking of all issued attestations

---

## 📊 Completion Proofs

### v0.1 Proof

```bash
python examples/v01_completion_demo.py
```

✅ Same prompt repeated 4 times → 1-3: STOP, 4: HOLD (adaptation applied)
✅ Judgments stored externally, patterns accumulated, behavior modified

### v0.2 Proof

```bash
python examples/v02_organizational_memory_demo.py
```

✅ 20 STOP judgments → VERY_CONSERVATIVE profile
✅ Runtime restart → Character persists
✅ New unseen prompts → Organizational tendency reflected

### v0.3 Proof

```bash
python examples/v03_governance_demo.py
```

✅ Profile → Human language (Paragraph/Bullet/Formal)
✅ Boundary declarations stored separately
✅ Human overrides excluded from pattern learning
✅ Full accountability & traceability

### v0.4 Proof

```bash
python examples/v04_attestation_demo.py
```

✅ Organizational character → Immutable attestation
✅ Attestation hash verifiable and reproducible
✅ Evidence pack generated (JSON + Markdown)
✅ External explanations ready (Auditor/Regulator/Contract)
✅ Attestation registry maintains history

---

## 📁 Project Structure

```
judgment-runtime/
├── src/
│   ├── judgment/
│   │   ├── decision.py              # [v0.1] Judgment Decision Module
│   │   ├── negative_proof.py        # [v0.1] Negative Proof Generator
│   │   ├── memory.py                # [v0.1] Judgment Memory Store
│   │   ├── adaptation.py            # [v0.1] Online Adaptation Engine
│   │   ├── aggregator.py            # [v0.2] Memory Aggregator
│   │   ├── profile_store.py         # [v0.2] Organization Profile Store
│   │   ├── explainer.py             # [v0.3] Boundary Profile Explainer
│   │   ├── declaration.py           # [v0.3] Boundary Declaration Store
│   │   ├── override.py              # [v0.3] Human Override Store
│   │   ├── diff.py                  # [v0.3] Boundary Diff Engine
│   │   ├── attestation/
│   │   │   ├── builder.py           # [v0.4] Attestation Builder
│   │   │   ├── evidence.py          # [v0.4] Evidence Pack Generator
│   │   │   ├── explainer.py         # [v0.4] External Explainer
│   │   │   └── registry.py          # [v0.4] Attestation Registry
│   │   └── runtime.py               # Main Runtime (v0.1-v0.4)
│   ├── models/
│   │   └── schemas.py               # Pydantic models
│   └── utils/
│       └── hashing.py               # Signature generation
├── tests/
├── examples/
│   ├── v01_completion_demo.py       # v0.1 proof
│   ├── v02_organizational_memory_demo.py  # v0.2 proof
│   ├── v03_governance_demo.py       # v0.3 proof
│   └── v04_attestation_demo.py      # v0.4 proof
├── pyproject.toml
└── README.md
```

---

## 🧪 Testing

```bash
# Run tests
python tests/test_decision.py
python tests/test_memory.py
python tests/test_runtime.py

# Run completion demos
python examples/v01_completion_demo.py
python examples/v02_organizational_memory_demo.py
python examples/v03_governance_demo.py
python examples/v04_attestation_demo.py
```

---

## 🛤️ Roadmap

* ✅ **v0.1**: External Accumulation Loop - Judgments can have memory
* ✅ **v0.2**: Organizational Memory Layer - Memory becomes organizational character
* ✅ **v0.3**: Boundary Governance & Override - Character is declared, explained, accountable
* ✅ **v0.4**: External Attestation Layer - Proof of what organization chose NOT to automate

**v0.4 Completion Statement:**

> **"이 시스템은 결정을 자동화하지 않는다.
> 조직이 어떤 결정을 자동화하지 않기로 했는지를 증명한다."**

---

## 🔐 Final Seal

### What This Is NOT

* ❌ AI model
* ❌ LLM platform
* ❌ RAG system
* ❌ Evaluation tool
* ❌ Governance dashboard
* ❌ Policy engine

### What This IS

> **"An infrastructure that remembers, explains, declares, and proves
> how an organization chooses NOT to use AI for certain decisions."**

**Key Properties:**

* Model-agnostic (works with any LLM)
* External state (no model modification)
* Deterministic and reproducible
* Verifiable and auditable
* Accountable by design

---

## 📄 License

MIT

---

## 👥 Contributing

Echo Judgment System is in architectural completion phase.
Extension proposals welcome after v0.4 stabilization.

---

**Built with:** Python 3.8+, Pydantic 2.0+

**Status:**
* ✅ v0.1 - External Accumulation Loop Complete
* ✅ v0.2 - Organizational Memory Layer Complete
* ✅ v0.3 - Boundary Governance & Override Complete
* ✅ v0.4 - External Attestation Layer Complete

**Architecture:** Model-Agnostic | External State | No Fine-tuning | Accountable
