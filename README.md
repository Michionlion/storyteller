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
│   ├── beat.md        # AI prose generation
│   └── critique.md    # AI critique generation
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
- **`prompts/critique.md`** - Controls how the AI critiques and reviews prose

The prompts are loaded automatically at runtime. Simply save changes and refresh the app.

### Streamlit Configuration

Edit `.streamlit/config.toml` to customize the UI theme and server settings.

## 📝 Workflow

### Basic Workflow (No Critique)

1. **Enter a seed idea** - A single sentence or phrase
2. **Generate Concept** - AI expands it into genre, setting, characters, conflict
3. **Generate Beats** - Add beat titles and AI writes immersive prose
4. **Add Facts** - Track narrative details for continuity (e.g., character traits, world rules)
5. **View Full Story** - See all beats compiled together
6. **Export** - Download your project as JSON

### Critique Loop Workflow (Recommended for Quality)

1. **Enable critique mode** - Toggle the "Enable critique loop" checkbox
2. **Generate beats** - AI writes initial drafts as usual
3. **Generate critique** - AI analyzes each beat and provides structured feedback
4. **Focus areas** - Specify what you want to improve (e.g., "add more sensory details")
5. **Improve beat** - AI rewrites based on critique + your focus areas
6. **Repeat** - Generate new critiques and improvements until satisfied
7. **Add facts** - Track narrative details for continuity
8. **View/Export** - Finalize and export your improved story

## 🔄 The Critique Loop

The critique loop is a powerful feature for iterative improvement:

```
Initial Draft → Generate Critique → Focus Areas → Improve Beat → Repeat
```

**Benefits:**
- Catch issues early before writing more
- Focus improvements on specific weaknesses
- Track the evolution of your writing
- Maintain continuity across revisions

**Example Flow:**
1. Generate a beat: "The hero enters the castle"
2. Generate critique: "The prose is flat, needs more sensory details"
3. Focus areas: "Describe the castle's atmosphere and the hero's nervousness"
4. Improve: "The iron door groaned as it opened, releasing a breath of stale, ancient air. The hero's heart pounded against their ribs as they stepped into the cavernous hall, shadows stretching like grasping fingers."

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
