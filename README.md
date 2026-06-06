# Alga Agent 🍀

<p align="center">
  <a href="docs/"><img src="https://img.shields.io/badge/Docs-alga--agent-FFD700?style=for-the-badge" alt="Documentation"></a>
  <a href="https://github.com/hahnavi/alga-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Lang-中文-red?style=for-the-badge" alt="中文"></a>
</p>

**Alga Agent is a self-improving AI agent for Alga.** It is a fork of the [Alga/hermes-agent](https://github.com/Alga/hermes-agent) framework. It features a built-in learning loop — it creates skills from experience, improves them during use, nudges itself to persist knowledge, searches its own past conversations, and builds a deepening model of who you are across sessions. Run it on a $5 VPS, a GPU cluster, or serverless infrastructure that costs nearly nothing when idle. It's not tied to your laptop — talk to it from Telegram while it works on a cloud VM.

Use any model you want — [OpenRouter](https://openrouter.ai) (200+ models), [NovitaAI](https://novita.ai) (AI-native cloud for Model API, Agent Sandbox, and GPU Cloud), [NVIDIA NIM](https://build.nvidia.com) (Nemotron), [Xiaomi MiMo](https://platform.xiaomimimo.com), [z.ai/GLM](https://z.ai), [Kimi/Moonshot](https://platform.moonshot.ai), [MiniMax](https://www.minimax.io), [Hugging Face](https://huggingface.co), OpenAI, or your own endpoint. Switch with `alga model` — no code changes, no lock-in.

<table>
<tr><td><b>A real terminal interface</b></td><td>Full TUI with multiline editing, slash-command autocomplete, conversation history, interrupt-and-redirect, and streaming tool output.</td></tr>
<tr><td><b>Lives where you do</b></td><td>Telegram, Discord, Slack, WhatsApp, Signal, and CLI — all from a single gateway process. Voice memo transcription, cross-platform conversation continuity.</td></tr>
<tr><td><b>A closed learning loop</b></td><td>Agent-curated memory with periodic nudges. Autonomous skill creation after complex tasks. Skills self-improve during use. FTS5 session search with LLM summarization for cross-session recall. <a href="https://github.com/plastic-labs/honcho">Honcho</a> dialectic user modeling. Compatible with the <a href="https://agentskills.io">agentskills.io</a> open standard.</td></tr>
<tr><td><b>Scheduled automations</b></td><td>Built-in cron scheduler with delivery to any platform. Daily reports, nightly backups, weekly audits — all in natural language, running unattended.</td></tr>
<tr><td><b>Delegates and parallelizes</b></td><td>Spawn isolated subagents for parallel workstreams. Write Python scripts that call tools via RPC, collapsing multi-step pipelines into zero-context-cost turns.</td></tr>
<tr><td><b>Runs anywhere, not just your laptop</b></td><td>Six terminal backends — local, Docker, SSH, Singularity, Modal, and Daytona. Daytona and Modal offer serverless persistence — your agent's environment hibernates when idle and wakes on demand, costing nearly nothing between sessions. Run it on a $5 VPS or a GPU cluster.</td></tr>
<tr><td><b>Research-ready</b></td><td>Batch trajectory generation, trajectory compression for training the next generation of tool-calling models.</td></tr>
</table>

---

## Quick Install

### Linux, macOS, WSL2, Termux

```bash
curl -fsSL https://raw.githubusercontent.com/hahnavi/alga-agent/main/scripts/install.sh | bash
```

### Windows (native, PowerShell)

> **Heads up:** Native Windows runs Alga without WSL — CLI, gateway, TUI, and tools all work natively. If you'd rather use WSL2, the Linux/macOS one-liner above works there too. Found a bug? Please [file issues](https://github.com/hahnavi/alga-agent/issues).

Run this in PowerShell:

```powershell
iex (irm https://raw.githubusercontent.com/hahnavi/alga-agent/main/scripts/install.ps1)
```

The installer handles everything: uv, Python 3.11, Node.js, ripgrep, ffmpeg, **and a portable Git Bash** (MinGit, unpacked to `%LOCALAPPDATA%\alga\git` — no admin required, completely isolated from any system Git install). Alga uses this bundled Git Bash to run shell commands.

If you already have Git installed, the installer detects it and uses that instead. Otherwise a ~45MB MinGit download is all you need — it won't touch or interfere with any system Git.

> **Android / Termux:** The tested manual path is documented in the [Termux guide](https://alga-agent.hahnavi.my.id/docs/getting-started/termux). On Termux, Alga installs a curated `.[termux]` extra because the full `.[all]` extra currently pulls Android-incompatible voice dependencies.
>
> **Windows:** Native Windows is fully supported — the PowerShell one-liner above installs everything. If you'd rather use WSL2, the Linux command works there too. Native Windows install lives under `%LOCALAPPDATA%\alga`; WSL2 installs under `~/.alga` as on Linux.

After installation:

```bash
source ~/.bashrc    # reload shell (or: source ~/.zshrc)
alga              # start chatting!
```

---

## Getting Started

```bash
alga              # Interactive CLI — start a conversation
alga model        # Choose your LLM provider and model
alga tools        # Configure which tools are enabled
alga config set   # Set individual config values
alga gateway      # Start the messaging gateway (Telegram, Discord, etc.)
alga setup        # Run the full setup wizard (configures everything at once)
alga claw migrate # Migrate from OpenClaw (if coming from OpenClaw)
alga update       # Update to the latest version
alga doctor       # Diagnose any issues
```

📖 **[Full documentation →](https://alga-agent.hahnavi.my.id/docs/)**

---

## CLI vs Messaging Quick Reference

Alga has two entry points: start the terminal UI with `alga`, or run the gateway and talk to it from Telegram, Discord, Slack, WhatsApp, Signal, or Email. Once you're in a conversation, many slash commands are shared across both interfaces.

| Action                         | CLI                                           | Messaging platforms                                                              |
| ------------------------------ | --------------------------------------------- | -------------------------------------------------------------------------------- |
| Start chatting                 | `alga`                                      | Run `alga gateway setup` + `alga gateway start`, then send the bot a message |
| Start fresh conversation       | `/new` or `/reset`                            | `/new` or `/reset`                                                               |
| Change model                   | `/model [provider:model]`                     | `/model [provider:model]`                                                        |
| Set a personality              | `/personality [name]`                         | `/personality [name]`                                                            |
| Retry or undo the last turn    | `/retry`, `/undo`                             | `/retry`, `/undo`                                                                |
| Compress context / check usage | `/compress`, `/usage`, `/insights [--days N]` | `/compress`, `/usage`, `/insights [days]`                                        |
| Browse skills                  | `/skills` or `/<skill-name>`                  | `/<skill-name>`                                                                  |
| Interrupt current work         | `Ctrl+C` or send a new message                | `/stop` or send a new message                                                    |
| Platform-specific status       | `/platforms`                                  | `/status`, `/sethome`                                                            |

For the full command lists, see the [CLI guide](https://alga-agent.hahnavi.my.id/docs/user-guide/cli) and the [Messaging Gateway guide](https://alga-agent.hahnavi.my.id/docs/user-guide/messaging).

---

## Documentation

All documentation is located inside the [website/docs/](website/docs/) directory.

| Section | Description |
| ------- | ----------- |
| [Quickstart](website/docs/getting-started/quickstart.md) | Install → setup → first conversation in 2 minutes |
| [CLI Usage](website/docs/user-guide/cli.md) | Commands, keybindings, personalities, sessions |
| [Configuration](website/docs/user-guide/configuration.md) | Config file, providers, models, all options |
| [Messaging Gateway](website/docs/user-guide/messaging/) | Telegram, Discord, Slack, WhatsApp, Signal, Home Assistant |
| [Security](website/docs/user-guide/security.md) | Command approval, DM pairing, container isolation |
| [Tools & Toolsets](website/docs/user-guide/features/tools.md) | 40+ tools, toolset system, terminal backends |
| [Skills System](website/docs/user-guide/features/skills.md) | Procedural memory, Skills Hub, creating skills |
| [Memory](website/docs/user-guide/features/memory.md) | Persistent memory, user profiles, best practices |
| [MCP Integration](website/docs/user-guide/features/mcp.md) | Connect any MCP server for extended capabilities |
| [Cron Scheduling](website/docs/user-guide/features/cron.md) | Scheduled tasks with platform delivery |
| [Context Files](website/docs/user-guide/features/context-files.md) | Project context that shapes every conversation |
| [Architecture](website/docs/developer-guide/architecture.md) | Project structure, agent loop, key classes |
| [Contributing](website/docs/developer-guide/contributing.md) | Development setup, PR process, code style |
| [CLI Reference](website/docs/reference/cli-commands.md) | All commands and flags |
| [Environment Variables](website/docs/reference/environment-variables.md) | Complete env var reference |

---

## Migrating from OpenClaw

If you're coming from OpenClaw, Alga can automatically import your settings, memories, skills, and API keys.

**During first-time setup:** The setup wizard (`alga setup`) automatically detects `~/.openclaw` and offers to migrate before configuration begins.

**Anytime after install:**

```bash
alga claw migrate              # Interactive migration (full preset)
alga claw migrate --dry-run    # Preview what would be migrated
alga claw migrate --preset user-data   # Migrate without secrets
alga claw migrate --overwrite  # Overwrite existing conflicts
```

What gets imported:

- **SOUL.md** — persona file
- **Memories** — MEMORY.md and USER.md entries
- **Skills** — user-created skills → `~/.alga/skills/openclaw-imports/`
- **Command allowlist** — approval patterns
- **Messaging settings** — platform configs, allowed users, working directory
- **API keys** — allowlisted secrets (Telegram, OpenRouter, OpenAI, Anthropic, ElevenLabs)
- **TTS assets** — workspace audio files
- **Workspace instructions** — AGENTS.md (with `--workspace-target`)

See `alga claw migrate --help` for all options, or use the `openclaw-migration` skill for an interactive agent-guided migration with dry-run previews.

---

## Contributing

We welcome contributions! See the [Contributing Guide](CONTRIBUTING.md) for development setup, code style, and PR process.

Quick start for contributors — clone and go with `setup-alga.sh`:

```bash
git clone https://github.com/hahnavi/alga-agent.git
cd alga-agent
./setup-alga.sh     # installs uv, creates venv, installs .[all], symlinks ~/.local/bin/alga
./alga              # auto-detects the venv, no need to `source` first
```

Manual path (equivalent to the above):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

---

## Community

- 📚 [Skills Hub](https://agentskills.io)
- 🐛 [Issues](https://github.com/hahnavi/alga-agent/issues)

---

## License

MIT — see [LICENSE](LICENSE).

