# storyteller

A minimal AI story writing tool for rapid prototyping.

## 🚀 Quick Start

```bash
# Install dependencies
pip install streamlit openai pydantic

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
├── tests/              # Test suite
│   └── test_storyteller.py
├── requirements.txt
└── README.md
```

## 🎯 Design Goals

- One file, minimal dependencies
- No database, in-memory storage
- Direct AI workflow exposure
- Testable with pytest

## 🧪 Testing

```bash
pytest tests/ -v
```

## 🔧 Customization

Edit the prompt files in `prompts/` to change AI behavior:

- `prompts/concept.md` - Controls how the AI generates story concepts
- `prompts/beat.md` - Controls how the AI writes prose for story beats

## 📝 License

MIT License
