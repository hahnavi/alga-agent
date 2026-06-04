# Langfuse Observability Plugin

This plugin ships bundled with Alga but is **opt-in** — it only loads when
you explicitly enable it.

## Enable

Pick one:

```bash
# Interactive: walks you through credentials + SDK install + enable
alga tools  # → Langfuse Observability

# Manual
pip install langfuse
alga plugins enable observability/langfuse
```

## Required credentials

Set these in `~/.alga/.env` (or via `alga tools`):

```bash
ALGA_LANGFUSE_PUBLIC_KEY=pk-lf-...
ALGA_LANGFUSE_SECRET_KEY=sk-lf-...
ALGA_LANGFUSE_BASE_URL=https://cloud.langfuse.com   # or your self-hosted URL
```

Without the SDK or credentials the hooks no-op silently — the plugin fails
open.

## Verify

```bash
alga plugins list                 # observability/langfuse should show "enabled"
alga chat -q "hello"              # then check Langfuse for a "Alga turn" trace
```

## Optional tuning

```bash
ALGA_LANGFUSE_ENV=production       # environment tag
ALGA_LANGFUSE_RELEASE=v1.0.0       # release tag
ALGA_LANGFUSE_SAMPLE_RATE=0.5      # sample 50% of traces
ALGA_LANGFUSE_MAX_CHARS=12000      # max chars per field (default: 12000)
ALGA_LANGFUSE_DEBUG=true           # verbose plugin logging
```

## Disable

```bash
alga plugins disable observability/langfuse
```
