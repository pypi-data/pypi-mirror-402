.PHONY: install lint format test build run kill deploy clean

# Install dependencies (frozen)
ci:
	uv sync --frozen $(if $(DEPLOY),--no-dev --no-install-project,--no-install-project)

# Install dependencies
install:
	uv sync --all-groups --no-install-project

# Run linting
lint:
	uv run ruff check .
	uv run ruff format --check .

# Format code
format:
	uv run ruff check --fix .
	uv run ruff format .

# Run tests
test:
	uv run pytest tests/ -v

# Run tests with coverage
cov:
	uv run pytest tests/ -v --cov --cov-report=term-missing

# Build Docker image
build:
	./scripts/build.sh

# Run Docker container
run:
	./scripts/run.sh

# Stop Docker container gracefully
kill:
	./scripts/kill.sh

# Deploy to AWS (use DRY=1 for dry-run)
deploy:
	DRY_RUN=$(if $(DRY),true,false) ./scripts/deploy.sh

# Update client versions from GitHub releases
update:
	uv run python scripts/update.py

# Clean build artifacts
clean:
	rm -rf .venv .pytest_cache __pycache__ .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

