# 🛑 Hardstop

> The mechanical brake for AI-generated commands

**Status:** Placeholder - Full release coming soon

## What is Hardstop?

Hardstop is a pre-execution safety system for AI-generated shell commands. It acts as a fail-closed verification layer, blocking dangerous patterns (like `rm -rf ~/`, reverse shells, credential exfiltration) before they execute.

**Two-layer defense:**
- **Pattern matching** — Instant regex-based detection
- **LLM analysis** — Semantic analysis for edge cases

## Key Features

- **Fail-closed design** — If safety check fails, command is blocked (not allowed)
- **Cross-platform** — Unix + Windows patterns
- **Command chaining** — Analyzes all parts of piped/chained commands
- **Audit logging** — All decisions logged

## Coming Soon

- Full Claude Code plugin release
- MCP server integration
- Configurable security policies

## Links

- [GitHub Repository](https://github.com/frmoretto/hardstop)

## License

CC-BY-4.0
