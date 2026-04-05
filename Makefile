.PHONY: dev frontend backend install build lint test clean

# Default target
all: dev

# Run both frontend and backend
dev:
	@echo "Starting frontend and backend..."
	cd frontend && npm run dev & \
	cd src && uv run uvicorn main:app --reload --port 8000

# Run only frontend
frontend:
	cd frontend && npm run dev

# Run only backend
backend:
	cd src && uv run uvicorn main:app --reload --port 8000

# Install all dependencies
install:
	cd src && uv sync
	cd frontend && npm install

# Build frontend for production
build:
	cd frontend && npm run build

# Run linter
lint:
	cd src && uv run ruff check .
	cd frontend && npm run lint 2>/dev/null || true

# Run tests
test:
	cd src && uv run pytest

# Clean up
clean:
	rm -f src/*.db src/*.lock
	cd frontend && rm -rf dist node_modules/.vite

# Help
help:
	@echo "Available targets:"
	@echo "  make dev      - Run both frontend and backend"
	@echo "  make frontend  - Run frontend only (http://localhost:5173)"
	@echo "  make backend  - Run backend only (http://localhost:8000)"
	@echo "  make install  - Install all dependencies"
	@echo "  make build    - Build frontend for production"
	@echo "  make lint     - Run linters"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean up generated files"
