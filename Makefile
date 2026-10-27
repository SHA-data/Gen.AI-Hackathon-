.PHONY: all test demo seed lint help

all: test

help:
	@echo "NeuralCFO + Moonshot Mode (Chatbot Module)"
	@echo "  make test   - Run all unit, integration, and contract test suites"
	@echo "  make demo   - Run the standalone gateway demo with active backend report"
	@echo "  make seed   - Seed demo organizations and user contexts"

test:
	python3 -m pytest tests/ -v

demo:
	@echo "=========================================================="
	@echo "Starting NeuralCFO + Moonshot Mode Gateway Demo"
	@echo "Active Backends:"
	@echo "  • FINANCE_BACKEND  : $${FINANCE_BACKEND:-fake (FakeFinanceService)}"
	@echo "  • MOONSHOT_BACKEND : $${MOONSHOT_BACKEND:-fake (FakeMoonshotWorkflow)}"
	@echo "  • MEMORY_BACKEND   : $${MEMORY_BACKEND:-meterless_fallback (MeterlessMemoryStore)}"
	@echo "  • LLM_MODEL        : $${MODEL_NAME:-nvidia/nemotron-3-super (FakeLLMProvider active)}"
	@echo "Gateway URL: http://localhost:8000"
	@echo "Web Shell  : http://localhost:3000"
	@echo "=========================================================="
	python3 -m uvicorn services.api.app.main:app --host 0.0.0.0 --port 8000 --reload

seed:
	python3 -c "from services.api.app.core.auth import DEMO_ORG_A, DEMO_ORG_B; print('Seeded Orgs:', DEMO_ORG_A, DEMO_ORG_B)"
