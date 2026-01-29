# TokTab CLI

> LLM pricing data at your fingertips

A command-line interface for accessing [TokTab](https://toktab.com/), a free API providing pricing data for 2000+ LLM models. Powered by [LiteLLM](https://github.com/BerriAI/litellm) and updated nightly.

## Installation

```bash
# Using uvx (recommended)
uvx toktab gpt-4o

# Or install with pip
pip install toktab
```

## Usage

### Get pricing info for a specific model

```bash
toktab gpt-4o
toktab claude-3-opus
toktab gemini-1-5-flash
```

Output:
```
╭──────────────────────────────────────────────────────────────────────────────╮
│ gpt-4o (openai)                                                               │
╰──────────────────────────────────────────────────────────────────────────────╯

Pricing
 Type    Cost / 1M tokens 
 Input              $2.50 
 Output            $10.00 

Context Window
 Limit       Tokens 
 Max input      128K 
 Max output      16K 

Capabilities
✓ Vision · ✓ Functions · ✓ Tool choice · ✓ System msgs
```

### Search for models

```bash
toktab search claude
toktab search "gemini 3"
toktab search provider:anthropic
```

### JSON output

All commands support `--json` for machine-readable output:

```bash
toktab --json gpt-4o
toktab search --json claude
```

### Options

```
Options:
  --json     Output raw JSON
  --version  Show version
  --help     Show this message and exit.
```

## Model Slugs

Model identifiers are derived from LiteLLM model names with special characters replaced by hyphens.  
For example:
- `gemini/gemini-pro` → `gemini-gemini-pro`
- `anthropic/claude-3-opus` → `anthropic-claude-3-opus`

Use the search command to find the exact slug for a model.

## Features

- 🚀 **Fast**: Lightweight CLI with minimal dependencies
- 📊 **Rich output**: Beautiful tables with cost color-coding (green=cheap, yellow=medium, red=expensive)
- 🔍 **Fuzzy search**: Find models by name or provider
- 💰 **Cost per million tokens**: Easy-to-read pricing format
- 🎨 **JSON output**: Perfect for scripting and automation
- 🆓 **Free**: No API key required

## Development

```bash
# Clone the repo
gh repo clone tomdyson/toktab-cli
cd toktab-cli

# Install with dev dependencies
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Run tests
pytest

# Test locally
toktab gpt-4o
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

- Data sourced from [LiteLLM](https://github.com/BerriAI/litellm)
- API provided by [TokTab](https://toktab.com/)
