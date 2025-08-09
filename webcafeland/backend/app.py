from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import re
import json
from dotenv import load_dotenv

# Try optional Anthropic import (fallback to heuristic if not available or no key)
try:
    import anthropic
    from anthropic.types.text_block import TextBlock
except Exception:
    anthropic = None
    TextBlock = None

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"ok": True})

# Analyze morphemes
@app.route('/api/analyze-morpheme', methods=['POST'])
def analyze_morpheme():
    data = request.get_json(silent=True) or {}
    word = (data.get('word') or '').strip()
    if not word:
        return jsonify({"error": "Missing word"}), 400

    atype = (data.get('type') or data.get('analysis_type') or 'morphemes').lower()

    # For morphemes-only (fast), keep the existing behavior
    if atype == 'morphemes':
        if ANTHROPIC_API_KEY and anthropic is not None:
            try:
                result = analyze_with_anthropic_morphemes(word)
                if result and isinstance(result, dict):
                    result["source"] = "anthropic"
                    return jsonify(result)
            except Exception as e:
                print("Anthropic error:", e)
        result = get_mock_analysis(word, analysis_type='morphemes')
        result["source"] = "heuristic"
        return jsonify(result)

    # For other tabs, derive from a single full analysis (Anthropic if available)
    full = None
    if ANTHROPIC_API_KEY and anthropic is not None:
        try:
            full = analyze_with_anthropic_full(word)
        except Exception as e:
            print("Anthropic full error:", e)

    if not isinstance(full, dict):
        # Heuristic fallback for non-morpheme tabs
        mock = get_mock_analysis(word, analysis_type='morphemes')
        full = {
            "word": word,
            "morphemes": mock.get("morphemes", []),
            "meaning": f"Definition unavailable for '{word}'.",
            "morphological_relatives": [],
            "etymological_relatives": [],
            "historical_origin": "",
            "graphemes": [{"grapheme": ch, "ipa": ""} for ch in re.findall(r"[A-Za-z]+|.", word) if ch.strip()]
        }

    def pick_piece(full_obj, t):
        if t == 'meaning':
            return {"meaning": full_obj.get("meaning", "")}
        if t == 'etymology':
            return {
                "historical_origin": full_obj.get("historical_origin", ""),
                "morphological_relatives": full_obj.get("morphological_relatives", []),
                "etymological_relatives": full_obj.get("etymological_relatives", [])
            }
        if t == 'graphemes':
            return {"graphemes": full_obj.get("graphemes", [])}
        if t == 'relatives':
            return {
                "morphological_relatives": full_obj.get("morphological_relatives", []),
                "etymological_relatives": full_obj.get("etymological_relatives", [])
            }
        # default: morphemes
        return {"word": full_obj.get("word", word), "morphemes": full_obj.get("morphemes", [])}

    piece = pick_piece(full, atype)
    piece["source"] = "anthropic" if ANTHROPIC_API_KEY and anthropic is not None else "heuristic"
    return jsonify(piece)

@app.route('/api/analyze-word', methods=['POST'])
def analyze_word_full():
    """Full analysis for a word: morphemes, meaning, relatives, etymology, graphemes."""
    data = request.get_json(silent=True) or {}
    word = (data.get('word') or '').strip()
    if not word:
        return jsonify({"error": "Missing word"}), 400

    if ANTHROPIC_API_KEY and anthropic is not None:
        try:
            result = analyze_with_anthropic_full(word)
            if isinstance(result, dict):
                result["source"] = "anthropic"
                return jsonify(result)
        except Exception as e:
            print("Anthropic full error:", e)

    # Fallback heuristic shape
    mock = get_mock_analysis(word, analysis_type='morphemes')
    result = {
        "word": word,
        "morphemes": mock.get("morphemes", []),
        "meaning": f"Definition unavailable for '{word}'.",
        "morphological_relatives": [],
        "etymological_relatives": [],
        "historical_origin": "",
        "graphemes": [{"grapheme": ch, "ipa": ""} for ch in re.findall(r"[A-Za-z]+|.", word) if ch.strip()],
        "source": "heuristic"
    }
    return jsonify(result)

def analyze_with_anthropic_morphemes(word):
    """Ask Anthropic for a JSON morpheme breakdown; robustly parse fenced code."""
    prompt = f"""
    Break the word "{word}" into morphemes and return JSON only.
    Schema:
    {{
      "word": "<word>",
      "morphemes": [{{ "morpheme": "<str>", "type": "prefix|root|suffix", "meaning": "<short>" }}]
    }}
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=400,
        temperature=0,
        system="Return only valid minified JSON. No prose.",
        messages=[{"role": "user", "content": prompt}],
    )

    content = None
    if TextBlock:
        content = next((b.text for b in response.content if isinstance(b, TextBlock)), None)
    if content is None:
        content = getattr(response, "content", "") or ""

    # strip code fences if present
    content = content.strip()
    if content.startswith("```"):
        first_nl = content.find("\n")
        content = content[first_nl + 1 :] if first_nl != -1 else content
    if content.endswith("```"):
        content = content[:-3]

    try:
        result = json.loads(content)
        if not isinstance(result, dict):
            raise ValueError("Not an object")
        result.setdefault("word", word)
        result.setdefault("morphemes", [])
        # Heuristic enrich: if Anthropic returned <=1 segment, try to add prefix/suffix/root
        if not isinstance(result.get("morphemes"), list) or len(result["morphemes"]) <= 1:
            fallback = get_mock_analysis(word).get("morphemes", [])
            if isinstance(fallback, list) and len(fallback) > len(result.get("morphemes", [])):
                result["morphemes"] = fallback
        return result
    except Exception as e:
        print("JSON parse error from Anthropic:", e, "content:", content)
        return {"word": word, "morphemes": get_mock_analysis(word).get("morphemes", [])}

def analyze_with_anthropic_full(word):
    """Anthropic prompt to return comprehensive JSON with morphemes, meaning, relatives, etymology, graphemes."""
    prompt = f"""
Break the word "{word}" into morphemes and graphemes, and return the result as a JSON object.
You are a linguist AI that breaks down English words into morphemes, graphemes, and explains their meaning, sound, and origin.

Given a word, return a structured JSON object with the following fields:
- "word": the original word
- "morphemes": a list of objects, each with:
  - "morpheme": the morpheme string (e.g. "un", "believe", "able"). Please note the root should be a real word (e.g. "believe" not "believ").
  - "type": one of "prefix", "root", or "suffix"
  - "meaning": a brief definition
- "meaning": a one-sentence overall definition of the word
- "morphological_relatives": a list of words that share both the root and base (e.g. "believe", "believable", "disbelievable")
- "etymological_relatives": a list of words that share the historical root only (e.g. "belief", "believer", "credence")
- "historical_origin": a brief description of the word's origin and evolution
- "graphemes": a list of objects, each with:
  - "grapheme": the letter or group of letters representing a sound (e.g., "ph", "a", "th")
  - "ipa": the corresponding IPA phonetic symbol (e.g., "f", "ə", "θ")

Return only valid JSON. Do not include any commentary or code fences.
"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=700,
        temperature=0,
        system="Return only valid minified JSON. No prose.",
        messages=[{"role": "user", "content": prompt}],
    )

    content = None
    if TextBlock:
        content = next((b.text for b in response.content if isinstance(b, TextBlock)), None)
    if content is None:
        content = getattr(response, "content", "") or ""
    content = content.strip()

    # Strip code fences if any slipped through
    if content.startswith("```"):
        first_nl = content.find("\n")
        content = content[first_nl + 1 :] if first_nl != -1 else content
    if content.endswith("```"):
        content = content[:-3]

    try:
        result = json.loads(content)
        if not isinstance(result, dict):
            raise ValueError("Not an object")
        # normalize/ensure fields
        result.setdefault("word", word)
        result.setdefault("morphemes", [])
        result.setdefault("meaning", "")
        result.setdefault("morphological_relatives", [])
        result.setdefault("etymological_relatives", [])
        result.setdefault("historical_origin", "")
        result.setdefault("graphemes", [])
        # Heuristic enrich morphemes if short
        if not isinstance(result.get("morphemes"), list) or len(result["morphemes"]) <= 1:
            fallback = get_mock_analysis(word).get("morphemes", [])
            if isinstance(fallback, list) and len(fallback) > len(result.get("morphemes", [])):
                result["morphemes"] = fallback
        return result
    except Exception as e:
        print("JSON parse error from Anthropic (full):", e, "content:", content)
        mock = get_mock_analysis(word)
        return {
            "word": word,
            "morphemes": mock.get("morphemes", []),
            "meaning": "",
            "morphological_relatives": [],
            "etymological_relatives": [],
            "historical_origin": "",
            "graphemes": []
        }

# Simple heuristic fallback that extracts prefix/root/suffix
def get_mock_analysis(word, analysis_type='morphemes'):
    w = re.sub(r"[^A-Za-z\-']", "", word)
    if not w or re.search(r"\d", w):
        return {"word": word, "morphemes": []}

    prefixes = {
        "anti": "against", "auto": "self", "bi": "two", "co": "together",
        "contra": "against", "de": "down/away", "dis": "not/opposite",
        "en": "cause to", "em": "cause to", "ex": "out", "fore": "before",
        "im": "not", "in": "not/into", "inter": "between", "mis": "wrongly",
        "non": "not", "over": "too much", "pre": "before", "pro": "forward",
        "re": "again", "sub": "under", "super": "above", "trans": "across",
        "un": "not", "under": "below"
    }
    suffixes = {
        "able": "capable of", "ible": "capable of", "al": "relating to",
        "ed": "past tense", "en": "made of", "er": "one who/more",
        "est": "most", "ful": "full of", "ic": "relating to", "ing": "action",
        "ion": "act/state", "tion": "act", "ation": "act",
        "ity": "state/quality", "ive": "tending to", "less": "without",
        "ly": "in the manner of", "ment": "result", "ness": "state",
        "ous": "full of", "s": "plural", "es": "plural"
    }

    # find longest matching prefix/suffix
    p = ""
    for cand in sorted(prefixes.keys(), key=len, reverse=True):
        if w.lower().startswith(cand):
            p = cand
            break

    s = ""
    for cand in sorted(suffixes.keys(), key=len, reverse=True):
        if w.lower().endswith(cand) and len(w) > len(cand):
            s = cand
            break

    start = len(p)
    end_trim = len(s)
    core = w[start: len(w) - (end_trim if end_trim else 0)]
    segments = []

    if p:
        segments.append({"morpheme": p, "type": "prefix", "meaning": prefixes[p]})
    if core:
        segments.append({"morpheme": core, "type": "root", "meaning": "root/base"})
    if s:
        segments.append({"morpheme": s, "type": "suffix", "meaning": suffixes[s]})

    if not segments:
        segments = [{"morpheme": word, "type": "root", "meaning": "root/base"}]

    return {"word": word, "morphemes": segments}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
