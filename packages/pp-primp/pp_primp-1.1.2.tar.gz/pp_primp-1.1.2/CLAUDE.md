# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PRIMP (Python Requests IMPersonate) - specifically **pp_primp** - is a high-performance Python HTTP client library that can impersonate web browsers by mimicking their headers and TLS/JA3/JA4/HTTP2 fingerprints. It's built as a Rust extension using PyO3 and the rquest library.

**Important**: This is a fork/variant with local dependencies:
- Uses local paths for `rquest` and `rquest-util` (see Cargo.toml lines 31, 45)
- Package name is `pp_primp` (not `primp`)
- Before building, ensure local dependencies are available at the specified paths

## Architecture

### Core Components

**Rust Layer (src/)**
- `lib.rs` - Main PyO3 module exposing `RClient` class with HTTP methods (get, post, etc.). Uses a global Tokio single-threaded runtime (`RUNTIME`) to execute async operations while releasing Python's GIL
- `random_impersonate.rs` - Browser/OS random impersonation logic. Supports selecting random versions from browser families (chrome, firefox, safari, edge, opera, okhttp) or "random"/"all" for any browser
- `header_order.rs` - Browser-specific header ordering (CHROME_HEADER_ORDER, FIREFOX_HEADER_ORDER, etc.) to match real browser behavior
- `response.rs` - Response handling with lazy content loading, encoding detection, and HTML conversion (text_markdown, text_plain, text_rich). Includes streaming support via `ResponseStream`
- `traits.rs` - Extension traits for converting between IndexMap and HeaderMap types, plus CookiesTraits for cookie string formatting
- `utils.rs` - CA certificate loading from environment variables (PRIMP_CA_BUNDLE or CA_CERT_FILE)

**Python Layer (pp_primp/)**
- `__init__.py` - Wraps Rust `RClient` with `Client` and `AsyncClient` classes. `AsyncClient` uses `asyncio.run_in_executor` to run synchronous methods asynchronously
- `pp_primp.pyi` - Type stubs for IDE support
- `pp_primp.pyd` - Compiled Rust extension (Windows)

### Key Design Patterns

1. **Lazy Loading**: Response properties (content, headers, cookies, encoding) are computed on first access and cached
2. **Thread Safety**: Client uses `Arc<Mutex<rquest::Client>>` for safe concurrent access
3. **GIL Release**: All I/O operations use `py.allow_threads()` to release Python's GIL during blocking operations
4. **Single Runtime**: Global Tokio single-threaded runtime (`RUNTIME`) shared across all client instances to avoid overhead
5. **Header Ordering**: Browser-specific header ordering maintained to match real browser fingerprints

## Development Commands

### Building

Build Rust extension in debug mode:
```bash
maturin develop
```

Build release version:
```bash
maturin build --release
```

Build with specific Python version:
```bash
maturin develop --python 3.12
```

**Note**: Ensure local dependencies (rquest, rquest-util) are available at paths specified in Cargo.toml before building.

### Testing

Run all tests:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/test_client.py
```

Run with verbose output:
```bash
pytest -v
```

Run specific test function:
```bash
pytest tests/test_client.py::test_client_init_params -v
```

### Linting & Type Checking

Format Python code:
```bash
ruff format pp_primp/ tests/
```

Lint Python code:
```bash
ruff check pp_primp/ tests/
```

Type check:
```bash
mypy pp_primp/
```

Format Rust code:
```bash
cargo fmt
```

Lint Rust code:
```bash
cargo clippy
```

### Benchmarking

Install benchmark dependencies:
```bash
pip install -r benchmark/requirements.txt
```

Start benchmark server:
```bash
uvicorn benchmark.server:app --host 0.0.0.0 --port 8000
```

Run benchmark (in separate terminal):
```bash
python benchmark/benchmark.py
```

Generate benchmark image:
```bash
python benchmark/generate_image.py
```

## Important Implementation Details

### Environment Variables

- `PRIMP_PROXY` - Default proxy URL if not specified in client
- `PRIMP_CA_BUNDLE` or `CA_CERT_FILE` - Path to custom CA certificate bundle (checked in that order)

### Client Initialization Flow

1. `impersonate_random` parameter is processed first if provided (selects random browser version)
2. Impersonation settings are applied (determines headers/TLS fingerprint)
3. Custom headers override default impersonation headers
4. Proxy is loaded from parameter or `PRIMP_PROXY` environment variable
5. CA certificates loaded from `ca_cert_file` parameter, environment variables, or defaults to rquest's webpki-roots

### Request Body Handling

Only POST, PUT, PATCH, DELETE methods support request bodies. Body types are mutually exclusive:
- `content` - Raw bytes
- `data` - Form-encoded data
- `json` - JSON-encoded data
- `files` - Multipart file upload

### Impersonate Latest Version Feature

**NEW**: When specifying only a browser name without a version number in the `impersonate` parameter, pp_primp will automatically use the latest available version for that browser:

- `impersonate="chrome"` → `chrome_143` (latest Chrome)
- `impersonate="firefox"` → `firefox_android_135` (latest Firefox)
- `impersonate="safari"` → `safari_ios_26.2` (latest Safari)
- `impersonate="edge"` → `edge_142` (latest Edge)
- `impersonate="opera"` → `opera_119` (latest Opera)
- `impersonate="okhttp"` → `okhttp_5` (latest OkHttp)

This is implemented in the Python layer (`pp_primp/__init__.py`) via the `_normalize_impersonate()` function, which converts browser names to `{browser}_latest` format. The Rust layer (`src/lib.rs` and `src/random_impersonate.rs`) then resolves `_latest` suffix to the actual latest version using the `latest_impersonate()` function.

Example usage:
```python
import pp_primp

# Use latest Chrome version
client = pp_primp.Client(impersonate="chrome")
print(client.impersonate)  # Output: chrome_143

# Specific versions still work
client = pp_primp.Client(impersonate="chrome_120")
print(client.impersonate)  # Output: chrome_120
```

### Impersonate Random Feature

The `impersonate_random` parameter allows selecting a random browser version:
- `"chrome"` - Random Chrome version
- `"firefox"` - Random Firefox version
- `"safari"` - Random Safari version
- `"edge"` - Random Edge version
- `"opera"` - Random Opera version
- `"okhttp"` - Random OkHttp version
- `"random"` or `"all"` - Random version from any browser

Implemented in `src/random_impersonate.rs` with predefined version lists for each browser family.

### Cookie Handling

The `split_cookie` parameter controls cookie header format:
- `true` - Send cookies in separate Cookie headers (HTTP/2 style)
- `false` - Combine cookies in one header (HTTP/1.1 style)
- `None` (default) - Auto-detect based on protocol

## CI/CD

The project uses GitHub Actions (`.github/workflows/build.yml`) for:
- Building wheels for Linux (x86_64), Windows (x64), macOS (x86_64, aarch64)
- Manual workflow dispatch with optional PyPI publishing
- Publishing to PyPI when triggered manually or on tag push (v*.*.*)

**Note**: ARM builds (aarch64, armv7) are commented out in the current workflow.

## Testing Patterns

Tests use a `@retry` decorator for flaky network operations (max 3 retries with 1s delay). They validate:
- Client initialization parameters
- Request methods (GET, POST, etc.) with various body types
- Cookie handling (get/set via `set_cookies()` and `get_cookies()`)
- Header management (including `headers_update()`)
- Authentication (basic and bearer)
- Proxy support
- Response properties (status_code, headers, cookies, content, json, text, text_markdown, text_plain, text_rich)
- Streaming responses via `resp.stream()`
- Async client functionality

Test files: `test_client.py`, `test_asyncclient.py`, `test_response.py`, `test_defs.py`.

## Local Development Setup

1. Ensure local dependencies are available:
   - `rquest` at `G:/myself_rust_p/rquest`
   - `rquest-util` at `G:/myself_rust_p/rquest-util`

2. Install development dependencies:
```bash
pip install -e ".[dev]"
```

3. Build the extension:
```bash
maturin develop
```

4. Run tests to verify:
```bash
pytest
```
