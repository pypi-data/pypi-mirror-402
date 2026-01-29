# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Package Management
- **Install dependencies**: `uv sync` (uses UV package manager with lock file)
- **Install dev dependencies**: `uv sync --group dev --group lint`

### Code Quality
- **Lint code**: `uv run ruff check`
- **Format code**: `uv run ruff format`
- **Fix auto-fixable issues**: `uv run ruff check --fix`

### Testing
- **Run tests**: `uv run pytest src/tests/`
- **Run specific test**: `uv run pytest src/tests/test_client.py::test_name`

### Build and Release
- **Build package**: `uv build`
- **Check version**: `python -c "import theforecastingcompany; print(theforecastingcompany.__version__)"`

## Architecture Overview

### Core Components

**TFCClient** (`src/theforecastingcompany/tfc_client.py`) - Main SDK interface
- `forecast()` - Generate forecasts for future periods
- `cross_validate()` - Perform time series cross-validation with historical data
- Handles data validation, API communication, and response processing

**API Models** (`src/theforecastingcompany/api.py`) - Pydantic models for API validation
- Request/response schemas for forecast and cross-validation endpoints
- Type-safe data structures with automatic validation

**Utils** (`src/theforecastingcompany/utils.py`) - Core utilities and configuration
- `TFCModels` enum - Available forecasting models (TimesFM_2, TabPFN_TS, TFCGlobal, ChronosBolt, Moirai, MoiraiMoe)
- Async request handling with httpx, retry logic, and rate limiting
- Data validation functions and helper utilities

### Key Design Patterns

**Async Request Processing**: Uses httpx with asyncio for concurrent API requests
- Configurable concurrency limits via semaphores
- Exponential backoff retry logic for failed requests
- Progress tracking with tqdm for long-running operations

**Data Structure Requirements**:
- `unique_id` column - Identifies individual time series
- `ds` column - Date/timestamp (datetime format)
- `target` column - Values to forecast
- Optional: `static_variables`, `future_variables`, `historical_variables`

**Model-Specific Features**:
- **TFCGlobal**: Supports new product forecasting (items without historical data)
- **All models**: Support external features (holidays/events) with country-specific data
- **Quantile predictions**: Returns 0.1, 0.4, 0.5, 0.9 quantiles by default

### API Integration

**Authentication**: Uses Bearer token from `TFC_API_KEY` environment variable
**Base URL**: `https://api.retrocast.com/`
**Key endpoints**: `/forecast` and `/cross-validate`

### Dependencies and Requirements

**Runtime**: Python 3.11+, httpx, pandas, pydantic, nest-asyncio, tqdm
**Development**: pytest (testing), ruff (linting/formatting)
**Package management**: UV with lock file for deterministic builds

### Code Quality Standards

**Ruff configuration**: 120 character line length, Python 3.12 target
**Enabled rules**: isort, bugbear, unused imports, bare except detection, print statement detection
**Test structure**: Located in `src/tests/` with pytest fixtures for fake time series generation