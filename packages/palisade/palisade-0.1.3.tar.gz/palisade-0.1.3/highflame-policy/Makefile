.PHONY: build test check fmt lint clean doc examples help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build the library
	cargo build

build-release: ## Build the library in release mode
	cargo build --release

test: ## Run all tests
	cargo test

test-verbose: ## Run tests with output
	cargo test -- --nocapture

check: ## Run cargo check
	cargo check

fmt: ## Format code
	cargo fmt

lint: ## Run clippy
	cargo clippy -- -D warnings

clean: ## Clean build artifacts
	cargo clean

doc: ## Generate documentation
	cargo doc --no-deps --open

doc-all: ## Generate documentation with dependencies
	cargo doc --open

examples: ## Run all examples
	@echo "Running basic_usage example..."
	cargo run --example basic_usage
	@echo ""
	@echo "Running service_policies example..."
	cargo run --example service_policies

example-basic: ## Run basic usage example
	cargo run --example basic_usage

example-services: ## Run service policies example
	cargo run --example service_policies

watch: ## Watch for changes and run tests
	cargo watch -x test

install-tools: ## Install development tools
	cargo install cargo-watch
	cargo install cargo-audit

audit: ## Check for security vulnerabilities
	cargo audit

coverage: ## Generate code coverage report (requires cargo-tarpaulin)
	cargo tarpaulin --out Html --output-dir coverage

bench: ## Run benchmarks
	cargo bench

all: fmt lint test ## Run format, lint, and test

ci: check lint test ## Run CI checks

setup: ## Setup development environment (check Rust installation)
	@echo "Checking development environment..."
	@command -v rustc >/dev/null 2>&1 || (echo "❌ Rust not found. Install with: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh" && exit 1)
	@command -v cargo >/dev/null 2>&1 || (echo "❌ Cargo not found. Please reinstall Rust." && exit 1)
	@echo "✓ Rust $(shell rustc --version)"
	@echo "✓ Cargo $(shell cargo --version)"
	@echo ""
	@echo "Building project..."
	@cargo build
	@echo ""
	@echo "✓ Setup complete! Run 'make test' to verify."

