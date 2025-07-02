from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
import json
from dotenv import load_dotenv
import anthropic

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
# OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')  # Removed OpenAI
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

print("ANTHROPIC_API_KEY:", ANTHROPIC_API_KEY[:8] if ANTHROPIC_API_KEY else None)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Morpheme Highlighter API is running!"})

@app.route('/api/analyze-morpheme', methods=['POST'])
def analyze_morpheme():
    """Analyze a word's morphemes using AI"""
    try:
        data = request.get_json()
        if not data or 'word' not in data:
            return jsonify({"error": "Word not provided"}), 400
        
        word = data['word'].strip().lower()
        if not word:
            return jsonify({"error": "Word cannot be empty"}), 400
        
        # Analyze the word using AI
        analysis = analyze_word_with_ai(word)
        return jsonify(analysis)
        
    except Exception as e:
        print(f"Error analyzing word: {str(e)}")
        return jsonify({"error": "Failed to analyze word"}), 500

def analyze_word_with_ai(word):
    """Analyze a word using Anthropic API only"""
    if ANTHROPIC_API_KEY:
        try:
            return analyze_with_anthropic(word)
        except Exception as e:
            print(f"Anthropic analysis failed: {str(e)}")
    # Fallback to mock data if no API key is available
    return get_mock_analysis(word)

def analyze_with_anthropic(word):
    """Analyze word using Anthropic Claude API"""

    prompt = f'Break the word "{word}" into morphemes and return the result as JSON.'

    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=1000,
        temperature=1,
        system="You are a morpheme analyzer. You will be given a word and you will need to analyze it and return the result as JSON.",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ])
    content = response.content[0].text.strip()
    print("HERE:", content)
    # Extract JSON from response
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        raise

def get_mock_analysis(word):
    """Provide mock analysis for demonstration purposes"""
    mock_data = {
        "disrespectfully": {
            "prefix": {"part": "dis", "meaning": "not / opposite of"},
            "root": {"part": "respect", "meaning": "to show regard"},
            "suffix1": {"part": "ful", "meaning": "full of"},
            "suffix2": {"part": "ly", "meaning": "in a way that..."},
            "example": "He spoke disrespectfully to the teacher.",
            "related": ["respect", "respectful", "disrespect"]
        },
        "unbelievable": {
            "prefix": {"part": "un", "meaning": "not"},
            "root": {"part": "believe", "meaning": "to accept as true"},
            "suffix1": {"part": "able", "meaning": "capable of"},
            "example": "The magician's trick was unbelievable.",
            "related": ["believe", "believeable", "incredible"]
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