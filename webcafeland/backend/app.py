from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
from dotenv import load_dotenv
import anthropic
from anthropic.types.text_block import TextBlock

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
print("ANTHROPIC_API_KEY:", ANTHROPIC_API_KEY[:8] if ANTHROPIC_API_KEY else None)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Morpheme Highlighter API is running!"})

@app.route('/api/analyze-morpheme', methods=['POST'])
def analyze_morpheme():
    try:
        data = request.get_json()
        word = data.get('word', '').strip().lower()
        if not word:
            return jsonify({"error": "Word cannot be empty"}), 400

        analysis = analyze_word_with_ai(word)
        return jsonify(analysis)
    except Exception as e:
        print(f"Error analyzing word: {str(e)}")
        return jsonify({"error": "Failed to analyze word"}), 500

def analyze_word_with_ai(word):
    if ANTHROPIC_API_KEY:
        try:
            return analyze_with_anthropic(word)
        except Exception as e:
            print(f"Anthropic analysis failed: {str(e)}")
    return get_mock_analysis(word)

def analyze_with_anthropic(word):
    prompt = f"""
Break the word \"{word}\" into morphemes and return the result as a JSON object. 
You are a linguist AI that breaks down English words into morphemes and explains their meaning and origin.

Given a word, return a structured JSON object with the following fields:

- "word": the original word
- "morphemes": a list of objects, each with:
  - "morpheme": the morpheme string (e.g. "un", "believe", "able")
  - "type": one of "prefix", "root", or "suffix"
  - "meaning": a brief definition
- "meaning": a one-sentence overall definition of the word
- "morphological_relatives": a list of words that share both the root and base (e.g. "believe", "believable", "disbelievable")
- "etymological_relatives": a list of words that share the historical root only (e.g. "belief", "believer", "credence")
- "historical_origin": a brief description of the word's origin and evolution

### Example:

Word: "unbelievable"

```json
{{
  "word": "unbelievable",
  "morphemes": [
    {{ "morpheme": "un", "type": "prefix", "meaning": "not" }},
    {{ "morpheme": "believe", "type": "root", "meaning": "accept as true" }},
    {{ "morpheme": "able", "type": "suffix", "meaning": "capable of" }}
  ],
  "meaning": "Something that cannot be believed",
  "morphological_relatives": ["believable", "unbelievably", "disbelievable"],
  "etymological_relatives": ["belief", "believer", "credence"],
  "historical_origin": "Old English, from Proto-Germanic *ga-laubjan, from PIE root *leubh- ('to care or believe')"
}}
```"""
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=1000,
        temperature=1,
        system="You are a morpheme analyzer. Return a JSON breakdown of the word's morphemes.",
        messages=[{"role": "user", "content": prompt}]
    )

    content = next((block.text.strip() for block in response.content if isinstance(block, TextBlock)), None)

    if content.startswith("```json"):
        content = content[7:]  # remove "```json\n"
    if content.endswith("```"):
        content = content[:-3]  # remove ending ``

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise

#def get_mock_analysis(word):
    mock_data = {
        "disrespectfully": {
            "prefix": {"part": "dis", "meaning": "not / opposite of"},
            "root": {"part": "respect", "meaning": "to show regard"},
            "suffix1": {"part": "ful", "meaning": "full of"},
            "suffix2": {"part": "ly", "meaning": "in a way that..."},
            "example": "He spoke disrespectfully to the teacher.",
            "related": ["respect", "respectful", "disrespect"]
        },
        "happiness": {
            "root": {"part": "happy", "meaning": "feeling joy"},
            "suffix1": {"part": "ness", "meaning": "state or quality of"},
            "example": "Her happiness was contagious.",
            "related": ["happy", "sadness", "joyfulness"]
        }
    }

    return mock_data.get(word, {
        "root": {"part": word, "meaning": "word root"},
        "example": f"The word '{word}' appears in this sentence.",
        "related": [word]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
