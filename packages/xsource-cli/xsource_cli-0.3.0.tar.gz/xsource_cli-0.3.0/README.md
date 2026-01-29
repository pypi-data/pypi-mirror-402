# XSource CLI

**AI Agent Security Scanner** - Free Tier (50 attack vectors)

Test your LLM endpoints for security vulnerabilities using curated OWASP-aligned attack vectors.

## Installation

```bash
pip install xsource-cli
```

## Quick Start

```bash
# Scan OpenAI endpoint (uses OPENAI_API_KEY env var)
export OPENAI_API_KEY=sk-...
xsource scan --provider openai

# Scan Anthropic Claude
export ANTHROPIC_API_KEY=sk-ant-...
xsource scan --provider anthropic

# Scan custom endpoint
xsource scan --url https://api.example.com/v1/chat --api-key sk-xxx

# Save report to file
xsource scan --provider openai --output report.json

# List available attack vectors
xsource vectors
```

## Attack Vector Categories

| Category | Vectors | Description |
|----------|---------|-------------|
| Prompt Injection | 10 | Direct & indirect instruction hijacking |
| Jailbreak | 15 | DAN, roleplay, encoding bypasses |
| PII Leakage | 10 | Email, SSN, credit card extraction |
| System Prompt Leak | 10 | Instruction disclosure attacks |
| MCP/Tool Abuse | 5 | Function calling vulnerabilities |

**Total: 50 vectors** (Free Tier)

## Output Example

```
╭─────────────────── Scan Summary ───────────────────╮
│ Security Score: 72.5/100 (MODERATE)                │
│                                                    │
│ Vectors Tested: 50                                 │
│ Vulnerabilities: 8                                 │
│ Safe: 42                                           │
╰────────────────────────────────────────────────────╯

Severity Breakdown:
  🔴 CRITICAL  ████░░░░░░░░░░░░░░░░ 2
  🟠 HIGH      ████████░░░░░░░░░░░░ 4
  🟡 MEDIUM    ████░░░░░░░░░░░░░░░░ 2
```

## Commands

| Command | Description |
|---------|-------------|
| `xsource scan` | Scan an LLM endpoint for vulnerabilities |
| `xsource vectors` | List available attack vectors |
| `xsource version` | Show version information |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |

## Upgrade

Want more attack vectors? Visit [xsourcesec.com/pricing](https://xsourcesec.com/pricing)

| Tier | Vectors | Features |
|------|---------|----------|
| **Free CLI** | 50 | Unlimited local scans |
| **Starter** | 150 | Cloud dashboard, reports |
| **Pro** | 750 | Multi-pass testing, API access |
| **Enterprise** | 1,500 | Full vector library, priority support |

API: `https://api.xsourcesec.com`

## License

MIT License

---

Made with ❤️ by [XSource Security](https://xsourcesec.com)
