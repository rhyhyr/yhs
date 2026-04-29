# Development Guide

This page explains how to work on the codebase safely and consistently.

## Project Structure

- `main.py`: application entry point
- `agent_runtime.py`: runtime orchestration
- `indexing/`: indexing pipeline and models
- `regression_test.py`: baseline verification flow

## Development Workflow

1. Create a feature branch from `main`.
2. Make small, focused commits.
3. Run local checks before pushing.
4. Open a pull request and request review.

## Local Validation

- Install dependencies first.
- Run basic execution path:

  ```bash
  python main.py
  ```

- Run regression checks when changing retrieval or indexing behavior.

## Troubleshooting During Development

- Runtime or dependency errors: [[Troubleshooting]]
- First-time environment setup: [[Getting Started]]

## Related Docs

- [[Home]]
- [[Getting Started]]
- [[Troubleshooting]]
