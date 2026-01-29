# DPO Reader

<p align="center">
  <em>Turn Discourse threads into podcasts. Each author gets their own voice.</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/dpo-reader/">
    <img src="https://img.shields.io/pypi/v/dpo-reader.svg" alt="PyPI Version">
  </a>
  <a href="https://pypi.org/project/dpo-reader/">
    <img src="https://img.shields.io/pypi/pyversions/dpo-reader.svg" alt="Python Versions">
  </a>
  <a href="https://github.com/JacobCoffee/dpo-reader/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/JacobCoffee/dpo-reader.svg" alt="License">
  </a>
</p>

---

I got tired of skimming long forum threads. DPO Reader converts them to audio so I can listen while doing other things. Point it at any Discourse thread and it'll synthesize the whole thing with different voices for each participant.

## Install

```bash
# uv (recommended)
uv tool install dpo-reader

# Or run directly without installing
uvx dpo-reader listen "https://discuss.python.org/t/your-thread"

# pipx works too
pipx install dpo-reader
```

## Usage

```bash
# Basic: generate audio and play it
dpo-reader listen "https://discuss.python.org/t/your-thread"

# Interactive TUI with read-along highlighting
dpo-reader listen "https://discuss.python.org/t/your-thread" --ui

# Start from a specific post (the /50 in the URL does this automatically)
dpo-reader listen "https://discuss.python.org/t/your-thread/12345/50" --ui

# Or explicitly with -s
dpo-reader listen "https://discuss.python.org/t/your-thread" -s 50

# Export without playing
dpo-reader export "https://discuss.python.org/t/your-thread" -o thread.wav

# See what you're getting into before generating
dpo-reader info "https://discuss.python.org/t/your-thread"
dpo-reader preview "https://discuss.python.org/t/your-thread"
```

## Options

```
-o, --output PATH         Output file (default: output.wav)
-e, --engine ENGINE       openai | bark | piper
-s, --start-post INT      Start from this post number
-n, --max-posts INT       Limit number of posts
--ui                      Interactive TUI with controls
--no-attribution          Skip "Author says:" prefix
--no-play                 Don't auto-play after generating
-c, --cache-dir PATH      Cache audio chunks (useful if generation crashes)
-p, --pause FLOAT         Seconds between posts (default: 1.5)
-f, --file PATH           Load from local JSON (testing)
```

## TTS Engines

| Engine | Quality | Speed | Notes |
|--------|---------|-------|-------|
| OpenAI | Best | Fast | Needs API key, costs money |
| Bark | Excellent | Slow (~10s/sentence) | Local, wants a GPU |
| Piper | Good | Fast (~0.1s/sentence) | Local, CPU-only |

**Bark** is the default. It runs locally and produces natural-sounding speech with good intonation. A GPU helps a lot but isn't strictly required.

**OpenAI** (`-e openai`) sounds the best if you have an API key. Get one at [platform.openai.com/api-keys](https://platform.openai.com/api-keys) and set `OPENAI_API_KEY` in your environment or a `.env` file.

**Piper** (`-e piper`) is the lightweight option. Install with `uv pip install dpo-reader[piper]`. Good for batch processing or machines without GPUs.

## TUI Controls

When using `--ui`:

| Key | Action |
|-----|--------|
| Space | Play/Pause |
| ←/→ | Skip 5 seconds |
| ↑/↓ | Speed up/down |
| n/p | Next/Previous post |
| l | Toggle logs |
| q | Quit |

## Requirements

Python 3.10-3.13. The `onnxruntime` dependency doesn't support 3.14 yet.

## Development

```bash
git clone https://github.com/JacobCoffee/dpo-reader.git
cd dpo-reader
make dev

make lint        # Linting
make type-check  # Type checking
make test        # Tests
make ci          # All of the above

# Test TTS locally
make test-listen  # Piper
make test-bark    # Bark
```

## License

MIT
