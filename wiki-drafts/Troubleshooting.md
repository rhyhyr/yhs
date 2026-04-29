# Troubleshooting

Use this page to resolve common setup and runtime issues.

## Common Issues

## 1) `ModuleNotFoundError`

### Cause

Dependencies are not installed in the active Python environment.

### Fix

```bash
pip install -r requirements.txt
```

Then retry running the app.

## 2) API key or credential errors

### Cause

Required environment variables are missing or invalid.

### Fix

- Check your environment variable names.
- Restart terminal/session after editing variables.

## 3) Startup succeeds but behavior is incorrect

### Cause

Index or cached artifacts are stale.

### Fix

- Rebuild the index artifacts.
- Re-run your regression scenario.

## Debug Flow

1. Confirm setup using [[Getting Started]].
2. Re-check workflow and validation steps in [[Development Guide]].
3. Reproduce with minimal input and compare logs.

## Related Docs

- [[Home]]
- [[Getting Started]]
- [[Development Guide]]
