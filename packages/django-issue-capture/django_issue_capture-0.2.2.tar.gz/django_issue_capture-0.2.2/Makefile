.PHONY: help install install-dev lint format check test test-verbose migrate makemigrations shell clean build start stop logs createsuperuser

# Server configuration
SERVER_PORT ?= 8000
PID_FILE = .server.pid
LOG_FILE = .server.log
DB_FILE = tests/test_db.sqlite3

help:
	@echo "Django Issue Capture - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install runtime dependencies"
	@echo "  make install-dev    Install all dependencies (runtime + dev)"
	@echo ""
	@echo "Quality:"
	@echo "  make lint           Run ruff linter"
	@echo "  make format         Auto-format code with ruff"
	@echo "  make typecheck      Run mypy type checking"
	@echo "  make check          Run all quality checks"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run test suite"
	@echo "  make test-verbose   Run tests with verbose output"
	@echo ""
	@echo "Django:"
	@echo "  make migrate        Run migrations"
	@echo "  make makemigrations Create new migrations"
	@echo "  make shell          Django shell"
	@echo "  make createsuperuser Create admin user"
	@echo ""
	@echo "Server:"
	@echo "  make start          Start development server (port $(SERVER_PORT))"
	@echo "  make stop           Stop development server"
	@echo "  make logs           View server logs (tail -f)"
	@echo ""
	@echo "Package:"
	@echo "  make build          Build package"
	@echo "  make clean          Clean generated files"

install:
	uv sync

install-dev:
	uv sync --extra dev

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

typecheck:
	uv run mypy src/

check: lint typecheck test

test:
	PYTHONPATH=. uv run python tests/manage.py test

test-verbose:
	PYTHONPATH=. uv run python tests/manage.py test --verbosity=2

migrate:
	PYTHONPATH=. uv run python tests/manage.py migrate

makemigrations:
	PYTHONPATH=. uv run python tests/manage.py makemigrations django_issue_capture

shell:
	PYTHONPATH=. uv run python tests/manage.py shell

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	rm -rf .venv/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf .pytest_cache/
	rm -f tests/test_db.sqlite3
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	uv build

# Database initialization (auto-runs if DB doesn't exist)
$(DB_FILE):
	@echo "Initializing database..."
	PYTHONPATH=. uv run python tests/manage.py migrate
	PYTHONPATH=. uv run python tests/manage.py setup_issue_templates
	@echo "Database initialized. Run 'make createsuperuser' to create an admin user."

# Create superuser interactively
createsuperuser:
	PYTHONPATH=. uv run python tests/manage.py createsuperuser

# Development server management
start: $(DB_FILE)
	@if [ -f $(PID_FILE) ] && kill -0 $$(cat $(PID_FILE)) 2>/dev/null; then \
		echo "Server already running (PID: $$(cat $(PID_FILE)))"; \
	else \
		echo "Starting development server on port $(SERVER_PORT)..."; \
		PYTHONPATH=. uv run python tests/manage.py runserver $(SERVER_PORT) > $(LOG_FILE) 2>&1 & \
		echo $$! > $(PID_FILE); \
		sleep 1; \
		if kill -0 $$(cat $(PID_FILE)) 2>/dev/null; then \
			echo "Server started (PID: $$(cat $(PID_FILE)))"; \
			echo "View logs: make logs"; \
			echo "Stop server: make stop"; \
		else \
			echo "Failed to start server. Check $(LOG_FILE) for errors."; \
			rm -f $(PID_FILE); \
			exit 1; \
		fi \
	fi

stop:
	@if [ -f $(PID_FILE) ]; then \
		PID=$$(cat $(PID_FILE)); \
		if kill -0 $$PID 2>/dev/null; then \
			echo "Stopping server (PID: $$PID)..."; \
			kill $$PID; \
			rm -f $(PID_FILE); \
			echo "Server stopped."; \
		else \
			echo "Server not running (stale PID file)."; \
			rm -f $(PID_FILE); \
		fi \
	else \
		echo "No PID file found. Server may not be running."; \
	fi

logs:
	@if [ -f $(LOG_FILE) ]; then \
		tail -f $(LOG_FILE); \
	else \
		echo "No log file found. Start the server first: make start"; \
	fi
