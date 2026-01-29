# Development Guide

This guide covers setting up your development environment, running tests, and contributing to the highflame Policy Framework.

## Prerequisites

- **Rust**: 1.70 or later
- **Cargo**: Comes with Rust
- **Git**: For version control

## Quick Start

### Install Rust

If you don't have Rust installed:

```bash
# macOS/Linux
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Or visit: https://rustup.rs
```

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/highflame-io/highflame-policy
cd highflame-policy

# Build the library
cargo build

# Run tests
cargo test
```

## Development Workflow

### Building

```bash
# Debug build
cargo build

# Release build (optimized)
cargo build --release

# Check code without building
cargo check

# Build with all features
cargo build --all-features
```

### Running Tests

```bash
# Run all Rust tests
cargo test

# Run tests with output
cargo test -- --nocapture

# Run specific test
cargo test test_basic_policy_evaluation

# Run tests for a specific module
cargo test --test integration_tests

# Run with coverage (requires tarpaulin)
cargo install cargo-tarpaulin
cargo tarpaulin --out Html --output-dir coverage
```

### Code Quality

```bash
# Format code
cargo fmt

# Check formatting
cargo fmt -- --check

# Run clippy (linter)
cargo clippy -- -D warnings

# Run clippy on all targets
cargo clippy --all-targets -- -D warnings

# Fix clippy suggestions automatically (be careful!)
cargo clippy --fix
```

### Running Examples

```bash
# Run basic usage example
cargo run --example basic_usage

# Run service policies example
cargo run --example service_policies

# Run Palisade example
cargo run --example palisade_usage
```

### Documentation

```bash
# Generate and open documentation
cargo doc --no-deps --open

# Generate with dependencies
cargo doc --open

# Check documentation links
cargo doc --no-deps
```

### Using Makefile

We provide a Makefile for common tasks:

```bash
# Show all available commands
make help

# Build the library
make build

# Run tests
make test

# Run tests with output
make test-verbose

# Format and lint
make fmt
make lint

# Generate documentation
make doc

# Run all examples
make examples

# Clean build artifacts
make clean

# Run CI checks (fmt, lint, test)
make ci
```

## Project Structure

```
highflame-policy/
├── src/                    # Rust source code
│   ├── lib.rs             # Public API
│   ├── core.rs            # Core traits
│   ├── engine.rs          # Cedar implementation
│   ├── entities.rs        # Entity/action types
│   ├── decision.rs        # Decision types
│   ├── request.rs         # Request builders
│   ├── config.rs          # Configuration
│   ├── loader.rs          # Policy loading
│   └── error.rs           # Error types
│
├── policies/              # Service-specific policies
│   ├── ramparts/
│   ├── guardrails/
│   └── palisade/
│
├── examples/              # Usage examples
│   ├── basic_usage.rs
│   ├── service_policies.rs
│   └── palisade_usage.rs
│
├── tests/                 # Integration tests
│   └── integration_tests.rs
│
├── docs/                  # Documentation
│   └── DEVELOPING.md      # This file
│
├── Cargo.toml            # Rust manifest
├── pyproject.toml        # Python project config
├── Makefile              # Build automation
└── README.md             # Main documentation
```

## Adding New Features

### Adding Entity Types

Edit `src/entities.rs`:

```rust
pub enum EntityType {
    // ... existing types
    
    /// Your new entity type
    NewType,
}

impl EntityType {
    pub fn as_str(&self) -> &str {
        match self {
            // ... existing matches
            Self::NewType => "NewType",
        }
    }
}
```

### Adding Action Types

Edit `src/entities.rs`:

```rust
pub enum ActionType {
    // ... existing actions
    
    /// Your new action
    NewAction,
}

impl ActionType {
    pub fn as_str(&self) -> &str {
        match self {
            // ... existing matches
            Self::NewAction => "new_action",
        }
    }
}
```

### Adding New Tests

Create tests in `tests/` or add to existing test files:

```rust
#[test]
fn test_your_feature() {
    let mut engine = CedarPolicyEngine::new().unwrap();
    engine.load_policies("permit(principal, action, resource);").unwrap();
    
    let request = PolicyRequest::builder()
        .principal(EntityType::User, "test")
        .action(ActionType::ReadFile)
        .resource(EntityType::FilePath, "/test.txt")
        .build()
        .unwrap();
    
    let decision = engine.evaluate(&request).unwrap();
    assert!(decision.is_allowed());
}
```

## Local Development with Palisade

If you're developing both highflame-policy and Palisade:

```bash
# 1. Clone both repos side by side
workspace/
├── highflame-policy/
└── highflame-palisade/

# 2. In Palisade, set up local override
cd highflame-palisade
cp .cargo/config.toml.example .cargo/config.toml

# 3. Edit highflame-policy
cd ../highflame-policy
vim src/entities.rs

# 4. Build Palisade (uses your local changes)
cd ../highflame-palisade/rust
cargo build
```

## Debugging

### Using rust-lldb/rust-gdb

```bash
# Debug a test
cargo test --no-run
rust-lldb target/debug/deps/integration_tests-<hash>

# Or with gdb
rust-gdb target/debug/deps/integration_tests-<hash>
```

### Print Debugging

Add to your code:
```rust
println!("Debug: {:?}", some_value);
dbg!(some_value);  // Better - shows file/line
```

Run with output:
```bash
cargo test -- --nocapture
```

### Logging

Enable tracing logs:
```bash
RUST_LOG=highflame_policy=debug cargo test
RUST_LOG=trace cargo run --example basic_usage
```

## Performance Profiling

```bash
# Install flamegraph
cargo install flamegraph

# Profile an example
cargo flamegraph --example basic_usage

# Profile tests
cargo flamegraph --test integration_tests
```

## Benchmarking

```bash
# Run benchmarks (if added)
cargo bench

# Profile benchmarks
cargo bench -- --profile-time=5
```

## Continuous Integration

Our CI runs these checks:

```bash
# Format check
cargo fmt -- --check

# Clippy
cargo clippy --all-targets -- -D warnings

# Tests
cargo test --all-features

# Examples
cargo run --example basic_usage
cargo run --example service_policies
```

You can run the full CI suite locally:
```bash
make ci
```

## Release Process

1. **Update version** in `Cargo.toml`
2. **Update CHANGELOG.md**
3. **Run full test suite**: `make ci`
4. **Create git tag**: `git tag v0.1.0`
5. **Push**: `git push origin v0.1.0`
6. **Publish** (when ready): `cargo publish`

## Common Issues

### Issue: Cargo can't find highflame-policy

**Solution**: If using git dependency in another project:
```bash
# Clear cache
rm -rf ~/.cargo/git/checkouts/highflame-policy-*

# Try again
cargo clean && cargo build
```

### Issue: Tests fail with policy parsing errors

**Solution**: Check your Cedar syntax in policy files:
```bash
# Validate policies
cargo test test_local_policy_cedar_loading
```

### Issue: Slow compile times

**Solutions**:
```bash
# Use incremental compilation (default in dev)
# Use parallel builds
cargo build -j8

# Use sccache
cargo install sccache
export RUSTC_WRAPPER=sccache
```

## Getting Help

- **Documentation**: Run `cargo doc --open`
- **Examples**: Check `examples/` directory
- **Tests**: Read `tests/` for usage patterns
- **Issues**: File on GitHub

## Code Style

We follow standard Rust conventions:

- Use `rustfmt` for formatting
- Follow clippy suggestions
- Write documentation for public APIs
- Add examples to docstrings
- Keep functions focused and small
- Use descriptive variable names

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `make test`
5. Run linters: `make lint`
6. Commit: `git commit -m "Add my feature"`
7. Push: `git push origin feature/my-feature`
8. Create a Pull Request

## Resources

- [Rust Book](https://doc.rust-lang.org/book/)
- [Cedar Policy Language](https://www.cedarpolicy.com/)
- [Cargo Book](https://doc.rust-lang.org/cargo/)
- [Rust by Example](https://doc.rust-lang.org/rust-by-example/)
