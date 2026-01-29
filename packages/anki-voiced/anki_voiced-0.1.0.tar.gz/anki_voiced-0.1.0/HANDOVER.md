# anki-voiced Handover Document

## Overview

**anki-voiced** is a CLI tool that generates Anki flashcard decks with AI-voiced audio. It takes CSV vocabulary files and produces `.apkg` files ready to import into Anki.

### Key Value Proposition

- **Zero manual audio work**: AI generates native-quality audio for every card
- **Multiple card types**: Comprehension + Production cards for active recall
- **Language support**: English, Japanese, French, Portuguese
- **Caching**: Audio is cached so re-running is fast

---

## Quick Start

```bash
cd /home/kakkoidev/Code/anki-voiced

# Install dependencies
uv sync --all-extras

# Create a sample project
uv run anki-voiced init --lang japanese

# Preview what would be created
uv run anki-voiced create vocabulary.csv --dry-run

# Generate the deck (this takes time - audio generation)
uv run anki-voiced create vocabulary.csv -o my-deck.apkg --lang japanese
```

---

## CLI Commands

### `anki-voiced create`

The main command. Generates a deck from CSV.

```bash
# Basic usage
uv run anki-voiced create vocab.csv

# With options
uv run anki-voiced create vocab.csv \
  --output my-deck.apkg \
  --name "Japanese IT Vocabulary" \
  --lang japanese \
  --voice male \
  --template double-card

# Dry run (no files created, just shows what would happen)
uv run anki-voiced create vocab.csv --dry-run

# Quiet mode (for scripts)
uv run anki-voiced create vocab.csv --quiet

# JSON output (for automation)
uv run anki-voiced create vocab.csv --json

# Force regenerate audio (ignore cache)
uv run anki-voiced create vocab.csv --force

# From stdin
cat data.csv | uv run anki-voiced create - -o deck.apkg
```

### `anki-voiced init`

Creates sample files to get started.

```bash
uv run anki-voiced init                        # English, double-card template
uv run anki-voiced init --lang japanese        # Japanese samples
uv run anki-voiced init --template basic       # Basic template
uv run anki-voiced init --template cloze       # Cloze template
```

Creates:
- `vocabulary.csv` - Sample vocabulary
- `deck.toml` - Configuration file

### `anki-voiced voices`

Lists available TTS voices.

```bash
uv run anki-voiced voices                      # All voices
uv run anki-voiced voices --lang japanese      # Japanese only
uv run anki-voiced voices --json               # JSON format
```

### `anki-voiced join`

Combines multiple decks into one.

```bash
uv run anki-voiced join tier1.apkg tier2.apkg \
  --output combined.apkg \
  --name "Complete Course"
```

---

## Templates

### 1. `double-card` (Default)

Best for language learning. Creates 2 cards per entry.

**CSV format:**
```csv
sentence,translation,pronunciation,tags
会議は10時に始まります。,The meeting starts at 10.,かいぎはじゅうじにはじまります,business
```

**Cards generated:**
- **Comprehension**: Audio + Sentence → Translation
- **Production**: Translation + Hint → Sentence + Audio

### 2. `basic`

Simple front/back cards. 1 card per entry.

**CSV format:**
```csv
front,back
Hello,Bonjour
```

### 3. `cloze`

Fill-in-the-blank cards.

**CSV format:**
```csv
text,extra
I {{c1::like}} apples.,verb: to enjoy
She {{c1::runs}} every {{c2::day}}.,two blanks = two cards
```

---

## Configuration

### Environment Variables

```bash
export ANKI_VOICED_LANG=japanese      # Default language
export ANKI_VOICED_VOICE=female       # Default voice
export ANKI_VOICED_TEMPLATE=basic     # Default template
export NO_COLOR=1                     # Disable colored output
```

### Project Config (`deck.toml`)

For multi-tier decks or project defaults:

```toml
name = "Japanese IT Vocabulary"
language = "japanese"
voice = "jm_kumo"
template = "double-card"
output = "japanese-it.apkg"

# Multi-tier (optional)
[[tiers]]
name = "Tier 1 - Basics"
data = "tier1.csv"

[[tiers]]
name = "Tier 2 - Intermediate"
data = "tier2.csv"
```

Use with:
```bash
uv run anki-voiced create --config deck.toml
```

### User Config (`~/.config/anki-voiced/config.toml`)

Personal defaults across all projects:

```toml
language = "japanese"
voice = "male"
```

### Precedence (highest to lowest)

1. CLI flags (`--lang japanese`)
2. Environment variables (`ANKI_VOICED_LANG`)
3. Project config (`deck.toml`)
4. User config (`~/.config/anki-voiced/config.toml`)
5. Built-in defaults

---

## Project Architecture

```
src/anki_voiced/
├── __init__.py          # Package exports
├── __main__.py          # python -m anki_voiced
├── cli.py               # Typer CLI commands
├── config.py            # XDG paths, env vars, TOML loading
├── models.py            # Pydantic models, language/voice mappings
├── audio.py             # Kokoro TTS, MP3 encoding, caching
├── deck.py              # genanki deck building
├── csv_utils.py         # CSV parsing per template
├── templates/
│   ├── __init__.py      # Template registry
│   ├── basic.py         # Basic template
│   ├── double_card.py   # Double-card template
│   └── cloze.py         # Cloze template
└── preprocessing/
    ├── __init__.py
    └── japanese.py      # Furigana extraction, IT terms
```

### Key Files

| File | Purpose |
|------|---------|
| `cli.py` | All CLI commands, argument parsing, output formatting |
| `models.py` | `DeckConfig`, `VocabEntry`, language/voice constants |
| `audio.py` | `AudioGenerator` class, MP3 encoding, cache management |
| `deck.py` | `DeckBuilder` class, genanki integration |
| `csv_utils.py` | `load_csv()`, column name mapping, validation |
| `config.py` | `Config` class, XDG paths, `load_toml_file()` |

### Data Flow

```
CSV File
    ↓
csv_utils.load_csv() → list[VocabEntry]
    ↓
AudioGenerator.generate_batch() → entries with audio_file set
    ↓
DeckBuilder.build() → .apkg file
```

---

## Key Classes

### `VocabEntry` (models.py)

Represents one vocabulary item:

```python
class VocabEntry(BaseModel):
    sentence: str           # Target language text
    translation: str        # Translation
    pronunciation: str      # Reading guide (optional)
    hint: str              # Hint for production card (optional)
    tags: list[str]        # Categories
    audio_file: str | None # Set after audio generation

    # For cloze template
    text: str              # Text with {{c1::cloze}}
    extra: str             # Additional info
```

### `DeckConfig` (models.py)

Configuration for deck generation:

```python
class DeckConfig(BaseModel):
    name: str
    language: str          # "english", "japanese", etc.
    voice: str             # "male", "female", or specific voice ID
    template: str          # "basic", "double-card", "cloze"
    output: Path
    force: bool            # Ignore cache
    dry_run: bool

    @property
    def resolved_voice(self) -> str:  # Gets actual Kokoro voice ID

    @property
    def lang_code(self) -> str:       # Gets Kokoro language code
```

### `AudioGenerator` (audio.py)

Handles TTS and caching:

```python
generator = AudioGenerator(config, quiet=False)

# Generate single audio
generator.generate_audio(text, output_path, preprocess=None)

# Generate batch with progress bar
entries, generated, cached = generator.generate_batch(
    entries,
    audio_dir,
    prefix="card",
    preprocess=get_preprocessor("japanese"),
)
```

### `DeckBuilder` (deck.py)

Creates Anki packages:

```python
builder = DeckBuilder(config)
output_path = builder.build(entries, audio_dir)
card_count = builder.get_card_count(entries)
```

---

## Japanese-Specific Features

### Furigana Support

Use 【】 brackets for readings:

```csv
会議【かいぎ】は10時【じ】に始【はじ】まります。
```

The `pronunciation` field should contain kana-only text for TTS:

```csv
sentence,translation,pronunciation
会議【かいぎ】は10時に...,The meeting...,かいぎはじゅうじに...
```

### IT Term Conversion

English IT terms are automatically converted:

| Input | TTS Output |
|-------|------------|
| API | エーピーアイ |
| GitHub | ギットハブ |
| Docker | ドッカー |
| EC2 | イーシーツー |

See `preprocessing/japanese.py` for the full mapping.

---

## Caching

Audio is cached in `~/.cache/anki-voiced/` using a hash of:
- Text content
- Voice ID
- Language

Benefits:
- Re-running is fast (cached audio is copied)
- Interrupted runs can resume
- Same sentences across projects share cache

Clear cache:
```bash
rm -rf ~/.cache/anki-voiced
```

---

## Testing

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=anki_voiced

# Specific test
uv run pytest tests/test_csv_utils.py::test_load_csv_basic_template -v
```

---

## Common Workflows

### Create a Japanese IT Deck

```bash
# 1. Create CSV with your vocabulary
cat > vocab.csv << 'EOF'
sentence,translation,pronunciation,tags
会議【かいぎ】は10時に始まります。,The meeting starts at 10.,かいぎはじゅうじにはじまります,meetings
プルリクエストをレビューしてください。,Please review my pull request.,プルリクエストをレビューしてください,development
EOF

# 2. Preview
uv run anki-voiced create vocab.csv --lang japanese --dry-run

# 3. Generate
uv run anki-voiced create vocab.csv --lang japanese -o japanese-it.apkg

# 4. Import into Anki
# File → Import → Select japanese-it.apkg
```

### Create a Multi-Tier Course

```bash
# 1. Create tier CSVs
# tier1.csv, tier2.csv, tier3.csv

# 2. Create config
cat > deck.toml << 'EOF'
name = "Japanese IT Course"
language = "japanese"
voice = "jm_kumo"
template = "double-card"
output = "japanese-it-complete.apkg"

[[tiers]]
name = "Tier 1 - Foundations"
data = "tier1.csv"

[[tiers]]
name = "Tier 2 - Development"
data = "tier2.csv"

[[tiers]]
name = "Tier 3 - Advanced"
data = "tier3.csv"
EOF

# 3. Generate
uv run anki-voiced create --config deck.toml
```

### Add a New Language

1. Add to `LANGUAGES` in `models.py`:
   ```python
   LANGUAGES = {
       ...
       "spanish": {"code": "e", "default_voice": "ef_maria"},
   }
   ```

2. Add voices to `VOICES` in `models.py`:
   ```python
   VOICES = {
       ...
       "spanish": {
           "male": ["em_carlos"],
           "female": ["ef_maria"],
       },
   }
   ```

3. Add alias to `LANGUAGE_ALIASES`:
   ```python
   LANGUAGE_ALIASES = {
       ...
       "es": "spanish",
   }
   ```

4. Add samples to `csv_utils.py` `create_sample_csv()`.

### Add a New Template

1. Create `templates/new_template.py`:
   ```python
   import genanki
   from ..models import VocabEntry

   MODEL_ID = 1607392322  # Unique ID

   def create_new_template_model() -> genanki.Model:
       return genanki.Model(...)

   class NewTemplate:
       name = "new-template"
       model = None

       @classmethod
       def get_model(cls) -> genanki.Model: ...

       @classmethod
       def create_note(cls, entry: VocabEntry, audio_ref: str) -> genanki.Note: ...

       @classmethod
       def get_required_columns(cls) -> list[str]: ...

       @classmethod
       def get_audio_text(cls, entry: VocabEntry) -> str: ...
   ```

2. Register in `templates/__init__.py`

3. Add to `TEMPLATES` in `models.py`

4. Add CSV validation in `csv_utils.py`

---

## Troubleshooting

### "espeak-ng not found"

```bash
sudo apt install espeak-ng  # Ubuntu/Debian
brew install espeak-ng      # macOS
```

### Audio generation is slow

- First run downloads Kokoro model (~1GB)
- Each sentence takes ~2-5 seconds
- Use `--force` only when needed (bypasses cache)

### "Unknown language" error

Check spelling. Use `uv run anki-voiced voices` to see available languages.

### CSV column not recognized

Check column names match expected patterns:
- `sentence` / `front` / `word` / `target`
- `translation` / `back` / `meaning` / `definition`

Use `--template` to specify which template to use.

---

## Files to Know

| Path | Purpose |
|------|---------|
| `pyproject.toml` | Package config, dependencies |
| `uv.lock` | Locked dependencies (commit this) |
| `samples/*.csv` | Example CSVs for each language |
| `docs/*.md` | User documentation |
| `tests/*.py` | Test files |

---

## Next Steps

1. Try creating a deck with the sample files
2. Explore the CLI help: `uv run anki-voiced --help`
3. Read the template code to understand card generation
4. Check `preprocessing/japanese.py` for the IT term dictionary
