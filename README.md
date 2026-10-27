# NeuralCFO + Moonshot Mode
> **Open Agent Hackathon 2026** · Master Specification v0.1  
> *Bold ideas with the numbers to check them.*

---

## 👥 Team Workstreams & Module Ownership

This repository is built as a **Modular Monolith** designed for seamless 3-person collaboration without code conflicts:

| Workstream | Module Owner | Primary Code Directory | Alembic Migrations | Web UI Sub-route | Key Responsibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LLM Chatbot Gateway & Chat** | **Aroon** | `/services/api/app/chat` | `0300-0399` | `/apps/web/src/app/chat` | Conversational gateway, router, tool registry, verifier (V1-V9), web shell host, SSE streaming |
| **NeuralCFO (Finance Engine)** | **Sharjeel** | `/services/api/app/cfo` | `0100-0199` | `/apps/web/src/app/cfo` | Cash runway engine, baseline forecast, scenarios (hiring, late payments), CSV import |
| **Moonshot Mode (Strategy)** | **Aleena** (`leena-77`) | `/services/api/app/moonshot` | `0200-0299` | `/apps/web/src/app/moonshot` | 6-card strategy pipeline, constraint intake, gating, scoring profiles, skeptic section |

---

## 🏛️ Repository Layout

```
.
├── apps/
│   └── web/                   # Next.js 14+ UI Shell (Aroon owns shell; teammates add sub-pages)
│       └── src/app/
│           ├── chat/          # Conversational interface + Evidence Drawer host (Aroon)
│           ├── cfo/           # Scenario comparison & cash dashboard (Sharjeel)
│           └── moonshot/      # Strategy card explorer & experiment plans (Aleena)
├── packages/
│   └── contracts/             # SINGLE SOURCE OF TRUTH (Shared Pydantic models, protocols & fakes)
│       ├── envelope.py        # Standard ToolResultEnvelope & ErrorEnvelope
│       ├── finance.py         # Frozen Finance Contract v1 + FakeFinanceService
│       ├── moonshot.py        # MoonshotWorkflow Protocol + FakeMoonshotWorkflow
│       ├── evidence.py        # Claims, evidence links, and resolver protocols
│       ├── llm.py             # LLMProvider protocol + FakeLLMProvider
│       └── memory.py          # MemoryStore protocol + Meterless / Postgres fakes
├── services/
│   └── api/
│       ├── app/
│       │   ├── core/          # Foundation Kit (Auth, JWT, audit logging, errors, evidence registry)
│       │   ├── chat/          # Chatbot module (Router, agents, tools, runtime, verifier)
│       │   ├── cfo/           # NeuralCFO module (Sharjeel's workspace)
│       │   └── moonshot/      # Moonshot Mode module (Aleena's workspace)
│       └── migrations/        # Alembic versions partitioned by owner ranges (0001-0399)
├── docs/                      # Per-module architecture, progress logs, and test reports
│   ├── chat/                  # Architecture & integration readiness reports
│   ├── cfo/                   # CFO engine notes
│   └── moonshot/              # Moonshot criteria & scoring notes
├── tests/                     # Test suites (contract, integration, and per-module tests)
│   ├── contract/              # Cross-module protocol tests
│   ├── chat/                  # Gateway, streaming, router, and verifier tests
│   ├── integration/           # End-to-end multi-tenant & Moonshot M1-M10 tests
│   ├── cfo/                   # CFO engine tests
│   └── moonshot/              # Moonshot workflow tests
├── Makefile                   # Single-command dev & test tasks
└── docker-compose.yml         # PostgreSQL 16 (pgvector) + Redis + FastAPI + Next.js
```

---

## ⚡ How to Integrate Seamlessly (Zero Conflicts)

### 1. The Core Invariant
> **Modules talk ONLY through:**
> 1. Typed Python interfaces in `/packages/contracts`
> 2. The HTTP API under `/v1`
> 
> **No module imports another module's internal code or directly queries another module's database tables.**

### 2. Independent Local Development (Runnable Fakes)
Every external service and peer module has a runnable **Fake** in `/packages/contracts`:
- Chat runs completely on its own using `FakeFinanceService` and `FakeMoonshotWorkflow`.
- When Sharjeel is ready to connect the real Finance Engine, simply toggle `FINANCE_BACKEND=real`.
- When Aleena is ready to connect the real Moonshot Engine, simply toggle `MOONSHOT_BACKEND=real`.

### 3. Database Migration Ranges
Never edit another owner's migration file:
- **`0001-0099`**: Core tables (`organizations`, `users`, `audit_logs`, `decision_runs`, `claims`, `evidence_links`)
- **`0100-0199`**: CFO tables (Sharjeel)
- **`0200-0299`**: Moonshot tables (Aleena)
- **`0300-0399`**: Chat tables (Aroon)

---

## 🚀 Quickstart & Commands

### 1. Install Dependencies
```bash
# Python dependencies
pip install -r <(echo "fastapi uvicorn pydantic pydantic-settings pyjwt httpx python-multipart pytest pytest-asyncio")

# Next.js web dependencies
cd apps/web && npm install && cd ../..
```

### 2. Run All Automated Tests
```bash
make test
```
*Executes all 26 unit, contract, multi-tenant isolation, verifier (V1-V9), evaluation runner (20/20 questions), and Moonshot M1-M10 tests.*

### 3. Start the Full-Stack Demo
```bash
# Terminal 1: API Gateway (Port 8000)
make demo

# Terminal 2: Web UI (Port 3000)
cd apps/web && npm run dev
```

Open your browser at **`http://localhost:3000`** to test:
- 💼 **Hiring & 30-Day Client Delay Scenario** with interactive 26-week runway forecast chart.
- 🚀 **Moonshot Mode Intake & Strategy Synthesis** with tappable clarification options.
- 🔗 **Clickable Evidence Badges** opening the slide-out Evidence Drawer.
- 📊 **Dashboard Action Proposals** with preview and admin approval card.
- 🧠 **Cross-Session Memory Recall** via Meterless adapter.
