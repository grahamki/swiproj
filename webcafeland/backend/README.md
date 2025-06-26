# Morpheme Highlighter Backend

Flask backend for the Morpheme Highlighter application that provides AI-powered morphological analysis.

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (optional):
```bash
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

4. Run the application:
```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/analyze-morpheme` - Analyze word morphemes
  - Request body: `{"word": "disrespectfully"}`
  - Response: JSON with morpheme breakdown, definitions, and related words

## AI Integration

The backend supports multiple AI providers:

1. **OpenAI GPT** (primary) - Uses GPT-3.5-turbo for morphological analysis
2. **Anthropic Claude** (fallback) - Uses Claude-3-Sonnet for analysis
3. **Mock Data** (fallback) - Provides sample analysis for demonstration

## Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key
- `ANTHROPIC_API_KEY` - Your Anthropic API key
- `PORT` - Server port (default: 5000)

## Development

The Flask app runs in debug mode by default. For production, set `debug=False` in `app.py`.

## Example Response

```json
{
  "prefix": {"part": "dis", "meaning": "not / opposite of"},
  "root": {"part": "respect", "meaning": "to show regard"},
  "suffix1": {"part": "ful", "meaning": "full of"},
  "suffix2": {"part": "ly", "meaning": "in a way that..."},
  "example": "He spoke disrespectfully to the teacher.",
  "related": ["respect", "respectful", "disrespect"]
}
``` 