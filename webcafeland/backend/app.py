from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

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
    """Analyze a word using OpenAI or Anthropic API"""
    
    # Try OpenAI first, then Anthropic as fallback
    if OPENAI_API_KEY:
        try:
            return analyze_with_openai(word)
        except Exception as e:
            print(f"OpenAI analysis failed: {str(e)}")
    
    if ANTHROPIC_API_KEY:
        try:
            return analyze_with_anthropic(word)
        except Exception as e:
            print(f"Anthropic analysis failed: {str(e)}")
    
    # Fallback to mock data if no API keys are available
    return get_mock_analysis(word)

def analyze_with_openai(word):
    """Analyze word using OpenAI API"""
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    prompt = f"""Break "{word}" into morphemes, define each, give related words and a sentence. Return JSON in this exact format:
{{
  "prefix": {{"part": "dis", "meaning": "not / opposite of"}},
  "root": {{"part": "respect", "meaning": "to show regard"}},
  "suffix1": {{"part": "ful", "meaning": "full of"}},
  "suffix2": {{"part": "ly", "meaning": "in a way that..."}},
  "example": "He spoke disrespectfully to the teacher.",
  "related": ["respect", "respectful", "disrespect"]
}}

Only return valid JSON, no other text."""
    
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {'role': 'system', 'content': 'You are a linguistic expert specializing in morphological analysis.'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.3,
        'max_tokens': 500
    }
    
    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
    response.raise_for_status()
    
    result = response.json()
    content = result['choices'][0]['message']['content'].strip()
    
    # Extract JSON from response
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to extract JSON if it's wrapped in other text
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        raise

def analyze_with_anthropic(word):
    """Analyze word using Anthropic Claude API"""
    headers = {
        'x-api-key': ANTHROPIC_API_KEY,
        'Content-Type': 'application/json',
        'anthropic-version': '2023-06-01'
    }
    
    prompt = f"""Break "{word}" into morphemes, define each, give related words and a sentence. Return JSON in this exact format:
{{
  "prefix": {{"part": "dis", "meaning": "not / opposite of"}},
  "root": {{"part": "respect", "meaning": "to show regard"}},
  "suffix1": {{"part": "ful", "meaning": "full of"}},
  "suffix2": {{"part": "ly", "meaning": "in a way that..."}},
  "example": "He spoke disrespectfully to the teacher.",
  "related": ["respect", "respectful", "disrespect"]
}}

Only return valid JSON, no other text."""
    
    data = {
        'model': 'claude-3-sonnet-20240229',
        'max_tokens': 500,
        'messages': [
            {'role': 'user', 'content': prompt}
        ]
    }
    
    response = requests.post('https://api.anthropic.com/v1/messages', headers=headers, json=data)
    response.raise_for_status()
    
    result = response.json()
    content = result['content'][0]['text'].strip()
    
    # Extract JSON from response
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to extract JSON if it's wrapped in other text
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