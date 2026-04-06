# storyteller

A minimal AI story writing tool for rapid prototyping.

## 🚀 Quick Start

```bash
# Install dependencies
pip install streamlit openai pydantic

# Set your OpenAI API key
export OPENAI_API_KEY="sk-..."

# Run the app
streamlit run storyteller.py
```

## 📁 Project Structure

```
storyteller/
├── storyteller.py      # Main application (single file)
├── prompts/            # Editable prompt templates
│   ├── concept.md     # AI concept generation
│   └── beat.md        # AI prose generation
├── .streamlit/         # Streamlit configuration
│   ├── config.toml    # Theme and settings
│   └── secrets.toml   # API key secrets (edit locally)
├── tests/              # Test suite
│   └── test_storyteller.py
├── requirements.txt
└── README.md
```

## 🎯 Design Goals

- **One file** - Single-file application for simplicity
- **Minimal dependencies** - Only Streamlit, OpenAI, Pydantic
- **In-memory storage** - No database, session state based
- **Direct AI workflow** - Exposes the AI generation pipeline
- **Testable** - Full pytest test suite

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=storyteller --cov-report=html
```

## 🔧 Customization

### Edit Prompts

Edit the prompt files in `prompts/` to change AI behavior:

- **`prompts/concept.md`** - Controls how the AI generates story concepts
- **`prompts/beat.md`** - Controls how the AI writes prose for story beats

The prompts are loaded automatically at runtime. Simply save changes and refresh the app.

### Streamlit Configuration

Edit `.streamlit/config.toml` to customize the UI theme and server settings.

## 📝 Workflow

1. **Enter a seed idea** - A single sentence or phrase
2. **Generate Concept** - AI expands it into genre, setting, characters, conflict
3. **Generate Beats** - Add beat titles and AI writes immersive prose
4. **Add Facts** - Track narrative details for continuity (e.g., character traits, world rules)
5. **View Full Story** - See all beats compiled together
6. **Export** - Download your project as JSON

## 🛠️ Development

```bash
# Install development dependencies
pip install pytest pytest-cov

# Run linter
ruff check .

# Format code
ruff format .
```

## 📝 License

MIT License
