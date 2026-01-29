# Tauro CLI Module

## Overview

The **Tauro CLI** is a sophisticated command-line interface designed to provide a premium developer experience (DX) when interacting with the Tauro Data Pipeline Framework. Beyond simple command execution, it integrates intelligent configuration discovery, advanced Spark error diagnostics, and a professional terminal user interface.

## Key Features

### 1. Intelligent Configuration Discovery
Automatically locate the best configuration file for your context using a weighted scoring system.
- Supports **YAML**, **JSON**, and **DSL** (Domain Specific Language) formats.
- Understands Medallion layers (Bronze, Silver, Gold).
- Handles multi-environment fallback chains (e.g., `sandbox_alice` -> `sandbox` -> `base`).

### 2. Smart Error Diagnostics
Tired of reading 100-line Spark Java stack traces? The CLI includes a **Spark Error Analyzer** that translates crpytic JVM errors into actionable human-readable messages.
- Identifies `UNRESOLVED_COLUMN`, `TYPE_MISMATCH`, `PARSE_EXCEPTION`, and more.
- Provides suggestions for column name corrections.
- Highlights relevant code snippets in the terminal.

### 3. Professional Terminal UX
Powered by the `rich` library, the CLI provides:
- **Process Separators**: Visual cues for different pipeline stages.
- **Dynamic Progress Bars**: Real-time status for data processing.
- **Formatted Tables**: Clean display of pipeline statuses and configurations.
- **Color-Coded Logs**: Differentiates between infrastructure, data, and validation logs.

## Command Reference

### `tauro run`
Directly execute batch pipelines.
```bash
tauro run --env dev --pipeline process_transactions --start-date 2023-01-01
```
- `--node`: Execute a specific node in the pipeline.
- `--dry-run`: Log actions without performing actual writes.
- `--validate-only`: Verify configuration without running Spark.

### `tauro stream`
Manage real-time streaming pipelines.
```bash
# Start a stream
tauro stream run --config streaming_cfg.py --pipeline real_time_events

# Check status
tauro stream status --config streaming_cfg.py

# Stop gracefully
tauro stream stop --config streaming_cfg.py --execution-id exec_123 --timeout 60
```

### `tauro template`
Generate project boilerplate and scaffolding.
```bash
tauro template --template medallion_basic --project-name my_new_project
```

### `tauro config`
Inspect and debug configuration discovery.
```bash
tauro config list-pipelines --env prod
```

## Directory Structure

```
cli/
├── cli.py              # Main entry point and argument parsing
├── core.py             # Core types, Enums, and environment logic
├── config.py           # Config loaders and auto-discovery engine
├── execution.py        # Pipeline execution orchestration
├── error_analyzer.py   # Intelligent Spark/Python diagnostic engine
├── rich_logger.py      # Rich-based terminal UI management
├── formatters.py       # Output formatting for tables and status
└── template.py         # Project scaffolding logic
```

## Architecture

The CLI module follows a decoupled architecture:

1.  **Parser Layer**: `cli.py` uses `argparse` to define a unified command structure.
2.  **Discovery Layer**: `config.py` resolves the logical flags (env, layer) into physical file paths.
3.  **Context Layer**: `execution.py` initializes the Tauro `Context` and prepares the environment (PYTHONPATH, secrets).
4.  **Presentation Layer**: `rich_logger.py` and `formatters.py` handle how information is presented to the user.

## Environment Fallback System

Tauro uses a canonical environment system defined in `core.py`:

| Target Env | Fallback Order |
| :--- | :--- |
| `prod` | `prod` -> `base` |
| `staging` | `staging` -> `prod` -> `base` |
| `sandbox` | `sandbox` -> `base` |
| `sandbox_user`| `sandbox_user` -> `sandbox` -> `base` |
| `dev` | `dev` -> `base` |

## Advanced Error Analysis

When a Spark job fails, the `SparkErrorAnalyzer` catches the exception and prints a formatted panel:

```text
┏━━━━━━━━━━━━━━━━━━━━━ Spark Error Detected ━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                                 ┃
┃  Type: Column Not Found 🔍                                      ┃
┃  Message: Cannot resolve 'transaction_amt'                      ┃
┃  Suggestion: Did you mean 'transaction_amount'?                 ┃
┃                                                                 ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## License

Copyright © 2025 Faustino Lopez Ramos. For licensing information, see the LICENSE file in the project root.
